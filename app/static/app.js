document.addEventListener('DOMContentLoaded', () => {
    // Show the result of a login we were just redirected back from
    showLoginOutcome();

    // Check Auth Status on load
    checkAuthStatus();

    // Tab switching
    const navItems = document.querySelectorAll('.nav-item');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const pageTitle = document.getElementById('page-title');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            if(item.classList.contains('disabled')) return;
            e.preventDefault();

            navItems.forEach(nav => nav.classList.remove('active'));
            tabPanes.forEach(tab => tab.classList.remove('active'));

            item.classList.add('active');
            const tabId = item.getAttribute('data-tab');
            document.getElementById(`tab-${tabId}`).classList.add('active');

            // Update title
            pageTitle.textContent = item.textContent.trim();

            // Load data based on tab
            if(tabId === 'courses') loadCourses();
            if(tabId === 'files') loadFiles();
            if(tabId === 'schedule') {
                loadSchedules();
                populateScheduleSelect();
            }
            if(tabId === 'ai-settings') loadAISettings();
        });
    });

    // Login button — a full page redirect, so no pop-up blocker can stop it.
    // Google sends the browser back to /api/auth/callback, which redirects here.
    document.getElementById('btn-login').addEventListener('click', (e) => {
        const btn = e.target.closest('.btn');
        btn.disabled = true;
        btn.textContent = 'Redirecting to Google...';
        setLoginError('');
        window.location.href = '/api/auth/login';
    });

    // Sync All button
    const btnSyncAll = document.getElementById('btn-sync-all');
    if(btnSyncAll) {
        btnSyncAll.addEventListener('click', () => {
            const icon = btnSyncAll.querySelector('i');
            if(icon) icon.classList.add('fa-spin');

            fetch('/api/courses/sync/all', {method: 'POST'})
                .then(r => r.json())
                .then(() => {
                    setTimeout(() => {
                        if(icon) icon.classList.remove('fa-spin');
                        alert('Sync all started in background!');
                    }, 1000);
                })
                .catch(err => {
                    if(icon) icon.classList.remove('fa-spin');
                    alert('Error starting sync: ' + err.message);
                });
        });
    }

    // Schedule form
    document.getElementById('form-schedule').addEventListener('submit', (e) => {
        e.preventDefault();
        const courseId = document.getElementById('schedule-course').value;
        const cron = document.getElementById('schedule-cron').value;

        fetch('/api/schedule', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                course_id: courseId,
                cron_expression: cron
            })
        }).then(r => r.json()).then(data => {
            loadSchedules();
        });
    });

    // AI Settings Form
    const aiProvider = document.getElementById('ai-provider');
    const groupApiKey = document.getElementById('group-api-key');
    const groupEndpoint = document.getElementById('group-endpoint');

    aiProvider.addEventListener('change', (e) => {
        if(e.target.value === 'ollama') {
            groupApiKey.style.display = 'none';
            groupEndpoint.style.display = 'block';
        } else {
            groupApiKey.style.display = 'block';
            groupEndpoint.style.display = 'none';
        }
    });

    document.getElementById('form-ai-settings').addEventListener('submit', (e) => {
        e.preventDefault();
        const provider = aiProvider.value;
        const apiKey = document.getElementById('ai-api-key').value;
        const endpoint = document.getElementById('ai-endpoint').value;

        fetch('/api/ai/settings', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                provider: provider,
                api_key: apiKey,
                endpoint: endpoint
            })
        }).then(r => r.json()).then(data => {
            alert('AI Settings saved successfully!');
        });
    });
});

function loadAISettings() {
    fetch('/api/ai/settings')
        .then(r => r.json())
        .then(data => {
            document.getElementById('ai-provider').value = data.provider || 'gemini';
            document.getElementById('ai-api-key').value = data.api_key || '';
            document.getElementById('ai-endpoint').value = data.endpoint || 'http://localhost:11434';

            // Trigger change event to update form UI
            document.getElementById('ai-provider').dispatchEvent(new Event('change'));
        });
}

function showLoginOutcome() {
    const params = new URLSearchParams(window.location.search);
    const error = params.get('auth_error');

    if(error) setLoginError(error);

    // Clean the address bar so a refresh does not replay the message
    if(error || params.get('auth')) {
        params.delete('auth');
        params.delete('auth_error');
        const query = params.toString();
        window.history.replaceState({}, '', window.location.pathname + (query ? '?' + query : ''));
    }
}

function setLoginError(message) {
    const box = document.getElementById('login-error');
    if(!box) return;

    box.textContent = message; // textContent: the message comes from a query string
    box.style.display = message ? 'block' : 'none';
}

function checkAuthStatus() {
    const statusContainer = document.getElementById('auth-status-container');
    const modal = document.getElementById('login-modal');
    const errorBox = document.getElementById('login-error');

    fetch('/api/auth/status')
        .then(response => response.json())
        .then(data => {
            if(data.authenticated) {
                statusContainer.innerHTML = '<p class="text-success" style="color:var(--success)"><i class="fa-solid fa-check-circle"></i> Google Connected</p>';
                modal.classList.remove('active');
                loadCourses(); // initial load
            } else {
                statusContainer.innerHTML = '<p class="text-danger" style="color:var(--danger)"><i class="fa-solid fa-triangle-exclamation"></i> Not Connected</p>';
                modal.classList.add('active');
                // A message from the redirect is more specific — keep it
                if(data.error && !errorBox.textContent) setLoginError(data.error);
            }
        })
        .catch(err => {
            statusContainer.innerHTML = '<p class="text-danger" style="color:var(--danger)"><i class="fa-solid fa-triangle-exclamation"></i> Server Unreachable</p>';
            modal.classList.add('active');
            setLoginError('Could not reach the server: ' + err.message);
        });
}

function loadCourses() {
    const grid = document.getElementById('courses-grid');
    const loading = document.getElementById('courses-loading');

    grid.innerHTML = '';
    loading.style.display = 'block';

    fetch('/api/courses/')
        .then(response => {
            if(response.status === 401) {
                // Token went away or expired — ask the user to sign in again
                document.getElementById('login-modal').classList.add('active');
                return response.json().then(data => Promise.reject(new Error(data.detail)));
            }
            return response.json();
        })
        .then(courses => {
            loading.style.display = 'none';
            window.allCourses = courses; // Cache for schedule select

            courses.forEach(course => {
                const card = document.createElement('div');
                card.className = 'card';

                const trackBtnClass = course.is_tracked ? 'btn-primary' : 'btn-outline';
                const trackBtnText = course.is_tracked ? 'Tracking' : 'Not Tracking';

                card.innerHTML = `
                    <h3>${course.name}</h3>
                    <p>${course.section || 'No section'}</p>
                    <div class="card-actions">
                        <button class="btn ${trackBtnClass} btn-track" data-id="${course.id}">
                            ${trackBtnText}
                        </button>
                        ${course.is_tracked ? `<button class="btn btn-outline btn-sync" data-id="${course.id}"><i class="fa-solid fa-rotate"></i> Sync</button>` : ''}
                    </div>
                    ${course.is_tracked ? `
                    <div class="card-actions" style="margin-top:0.5rem; justify-content: flex-start; gap: 0.5rem;">
                        <a href="/api/export/${course.id}/zip" target="_blank" class="btn btn-outline" title="Export ZIP for NotebookLM">
                            <i class="fa-solid fa-file-zipper"></i> ZIP
                        </a>
                        <a href="/api/export/${course.id}/text" target="_blank" class="btn btn-outline" title="Export combined text for ChatGPT">
                            <i class="fa-solid fa-file-lines"></i> Text
                        </a>
                    </div>` : ''}
                `;
                grid.appendChild(card);
            });

            // Add listeners
            document.querySelectorAll('.btn-track').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const id = e.target.closest('.btn-track').getAttribute('data-id');
                    const courseName = courses.find(c=>c.id==id)?.name || "";
                    fetch(`/api/courses/${id}/track?name=${encodeURIComponent(courseName)}`, {method: 'POST'})
                        .then(() => loadCourses())
                        .catch(err => alert('Error tracking course: ' + err.message));
                });
            });

            document.querySelectorAll('.btn-sync').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const btn = e.target.closest('.btn');
                    const id = btn.getAttribute('data-id');

                    const icon = btn.querySelector('i');
                    if(icon) icon.classList.add('fa-spin');

                    fetch(`/api/courses/${id}/sync`, {method: 'POST'})
                        .then(r => r.json())
                        .then(() => {
                            setTimeout(() => {
                                if(icon) icon.classList.remove('fa-spin');
                                alert('Sync started in background');
                            }, 1000);
                        })
                        .catch(err => {
                            if(icon) icon.classList.remove('fa-spin');
                            alert('Error starting sync: ' + err.message);
                        });
                });
            });
        })
        .catch(err => {
            loading.style.display = 'none';
            const msg = document.createElement('p');
            msg.style.cssText = 'grid-column: 1/-1; color: var(--danger)';
            msg.textContent = 'Could not load courses: ' + err.message;
            grid.innerHTML = '';
            grid.appendChild(msg);
        });
}

function loadFiles() {
    const tbody = document.getElementById('files-table-body');
    tbody.innerHTML = '<tr><td colspan="5">Loading...</td></tr>';

    fetch('/api/files/')
        .then(response => response.json())
        .then(data => {
            tbody.innerHTML = '';

            if(data.items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5">No files downloaded yet.</td></tr>';
                return;
            }

            data.items.forEach(file => {
                const tr = document.createElement('tr');
                const sizeMb = file.file_size ? (file.file_size / (1024*1024)).toFixed(2) + ' MB' : 'Unknown';
                const date = new Date(file.downloaded_at).toLocaleString();

                tr.innerHTML = `
                    <td>${file.filename}</td>
                    <td>${file.course_name}</td>
                    <td>${sizeMb}</td>
                    <td>${date}</td>
                    <td>
                        <div style="display:flex;gap:0.5rem;align-items:center;">
                            <a href="/api/files/${file.id}/download" class="btn btn-outline" target="_blank" title="Download">
                                <i class="fa-solid fa-download"></i>
                            </a>
                            <button class="btn btn-outline btn-summarize" data-id="${file.id}" title="Summarize with AI">
                                <i class="fa-solid fa-wand-magic-sparkles"></i>
                            </button>
                        </div>
                    </td>
                `;
                tbody.appendChild(tr);

                // Add summary row
                const trSummary = document.createElement('tr');
                trSummary.style.display = 'none';
                trSummary.id = `summary-row-${file.id}`;
                trSummary.innerHTML = `
                    <td colspan="5">
                        <div class="summary-box" style="padding: 1rem; background: var(--bg-color); border: 1px solid var(--border-color); border-radius: 4px; margin-top: 0.5rem; white-space: pre-wrap;">
                            <strong style="display:block; margin-bottom: 0.5rem;"><i class="fa-solid fa-robot"></i> AI Summary:</strong>
                            <div id="summary-content-${file.id}">Loading summary...</div>
                        </div>
                    </td>
                `;
                tbody.appendChild(trSummary);
            });

            // Add listeners for summarize buttons
            document.querySelectorAll('.btn-summarize').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const id = e.target.closest('.btn-summarize').getAttribute('data-id');
                    const row = document.getElementById(`summary-row-${id}`);
                    const content = document.getElementById(`summary-content-${id}`);
                    const icon = e.target.closest('.btn-summarize').querySelector('i');

                    if(row.style.display === 'none') {
                        row.style.display = 'table-row';

                        // Check if we already have it
                        fetch(`/api/ai/summary/${id}`)
                            .then(r => r.json())
                            .then(data => {
                                if(data.summary) {
                                    content.innerHTML = data.summary;
                                } else {
                                    // Trigger summarize
                                    icon.classList.add('fa-spin');
                                    fetch(`/api/ai/summarize/${id}`, {method: 'POST'})
                                        .then(r => r.json())
                                        .then(resp => {
                                            content.innerHTML = "<em>Summarization started in background... Please refresh or click again in a moment.</em>";
                                            setTimeout(() => { icon.classList.remove('fa-spin'); }, 2000);
                                        });
                                }
                            });
                    } else {
                        row.style.display = 'none';
                    }
                });
            });
        });
}

function loadSchedules() {
    const grid = document.getElementById('schedule-grid');
    grid.innerHTML = 'Loading...';

    fetch('/api/schedule/')
        .then(response => response.json())
        .then(schedules => {
            grid.innerHTML = '';

            if(schedules.length === 0) {
                grid.innerHTML = '<p style="grid-column: 1/-1">No active schedules.</p>';
                return;
            }

            schedules.forEach(sched => {
                const card = document.createElement('div');
                card.className = 'card';
                card.innerHTML = `
                    <h3>${sched.course_name}</h3>
                    <p>Cron: <code>${sched.cron_expression}</code></p>
                    <div class="card-actions">
                        <span><i class="fa-solid fa-circle-check text-success"></i> Active</span>
                        <button class="btn btn-outline btn-delete-sched" data-id="${sched.course_id}">
                            <i class="fa-solid fa-trash text-danger"></i>
                        </button>
                    </div>
                `;
                grid.appendChild(card);
            });

            document.querySelectorAll('.btn-delete-sched').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const id = e.target.closest('.btn').getAttribute('data-id');
                    fetch(`/api/schedule/${id}`, {method: 'DELETE'})
                        .then(() => loadSchedules());
                });
            });
        });
}

function populateScheduleSelect() {
    if(!window.allCourses) return;

    const select = document.getElementById('schedule-course');
    select.innerHTML = '';

    window.allCourses.filter(c => c.is_tracked).forEach(course => {
        const opt = document.createElement('option');
        opt.value = course.id;
        opt.textContent = course.name;
        select.appendChild(opt);
    });
}
