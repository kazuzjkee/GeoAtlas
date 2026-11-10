let allResults = [];
    let allGroups = [];
    let activeSession = null;
    let sessionCountdownTimer = null;
    let allKnownStudents = [];
    let activeFilter = 'all';
    let searchQuery = '';
    let currentTeacher = null;
    let allTeachers = [];
    let rawServerResults = [];
    let rawServerGroups = [];

    const DEFAULT_PRESET_GROUPS = [
        {
            id: "grp-geofak-51",
            name: "Геофак-51 (ВКР)",
            description: "5 курс, профиль: География и Экономика (ВКР)",
            students: [
                { name: "Литвинов Е. К.", email: "elitvinov@sfedu.ru" },
                { name: "Иванов И. И.", email: "ivanov@sfedu.ru" },
                { name: "Сидорова М. В.", email: "sidorova@sfedu.ru" }
            ],
            created_at: "26.10.2026 10:00"
        },
        {
            id: "grp-econom-31",
            name: "Эконом-31 (ЮФО)",
            description: "3 курс, экономический анализ и ВРП",
            students: [
                { name: "Петров А. С.", email: "petrov@sfedu.ru" }
            ],
            created_at: "26.10.2026 10:00"
        },
        {
            id: "grp-geofak-41",
            name: "Геофак-41 (Бакалавриат)",
            description: "4 курс, картография и ГИС",
            students: [
                { name: "Ковалев Д. В.", email: "kovalev@sfedu.ru" },
                { name: "Смирнова А. А.", email: "smirnova@sfedu.ru" }
            ],
            created_at: "26.10.2026 10:00"
        }
    ];

    function initData() {
        // 0. Загрузка профиля преподавателя и списка преподавателей (B2B SaaS Мультитенантность)
        try {
            const teacherRaw = document.getElementById('server-teacher-data')?.textContent.trim();
            if (teacherRaw && teacherRaw !== '__SERVER_TEACHER_JSON__') {
                currentTeacher = JSON.parse(teacherRaw);
            }
        } catch (e) {}

        try {
            const allTRaw = document.getElementById('server-all-teachers-data')?.textContent.trim();
            if (allTRaw && allTRaw !== '__SERVER_ALL_TEACHERS_JSON__') {
                allTeachers = JSON.parse(allTRaw);
            }
        } catch (e) {}

        if (currentTeacher) {
            const orgTitle = document.getElementById('portal-org-title');
            const teacherNameEl = document.getElementById('teacher-fullname');
            const teacherOrgEl = document.getElementById('teacher-org');
            const teacherIdBadge = document.getElementById('teacher-id-badge');

            if (teacherNameEl && currentTeacher.full_name) {
                teacherNameEl.textContent = currentTeacher.full_name;
            }
            if (teacherOrgEl && currentTeacher.organization) {
                teacherOrgEl.textContent = currentTeacher.organization;
            }
            if (orgTitle && currentTeacher.organization) {
                orgTitle.textContent = `${currentTeacher.organization} — Панель преподавателя`;
            }
            if (teacherIdBadge) {
                teacherIdBadge.textContent = currentTeacher.teacher_id || currentTeacher.username;
            }
        }

        // 1. Загрузка результатов с сервера
        let serverResultsLoaded = false;
        try {
            const raw = document.getElementById('server-results-data').textContent.trim();
            if (raw && raw !== '__SERVER_RESULTS_JSON__') {
                allResults = JSON.parse(raw);
                serverResultsLoaded = true;
            }
        } catch (e) {
            allResults = [];
        }

        if (!serverResultsLoaded) {
            try {
                const local = localStorage.getItem('rostovQuizResults');
                if (local) {
                    const parsed = JSON.parse(local);
                    if (Array.isArray(parsed) && parsed.length > 0) {
                        allResults = parsed.map(r => ({
                            date: r.date,
                            name: r.student || r.name || 'Анонимно',
                            email: r.email || '-',
                            group: r.group || 'Не указана',
                            quiz_type: r.type || r.quiz_type || 'Общий',
                            score: r.score,
                            max_score: r.maxScore || r.max_score,
                            accuracy: r.accuracy,
                            time_spent: r.time_spent,
                            is_exam: !!r.is_exam,
                            exam_token: r.exam_token || '',
                            violations: r.violations || 0,
                            exam_status: r.exam_status || 'Сдано',
                            session_id: r.session_id || ''
                        }));
                    }
                }
            } catch (e) {}
        }

        // 2. Загрузка групп с сервера
        let serverGroupsLoaded = false;
        try {
            const grpRaw = document.getElementById('server-groups-data')?.textContent.trim();
            if (grpRaw && grpRaw !== '__SERVER_GROUPS_JSON__') {
                allGroups = JSON.parse(grpRaw);
                serverGroupsLoaded = true;
            }
        } catch (e) {}

        if (!serverGroupsLoaded) {
            try {
                const localGrp = localStorage.getItem('sfeduGroups');
                if (localGrp) allGroups = JSON.parse(localGrp);
            } catch(e) {}
        }
        if (!allGroups || allGroups.length === 0) {
            allGroups = DEFAULT_PRESET_GROUPS.slice();
            localStorage.setItem('sfeduGroups', JSON.stringify(allGroups));
        }

        // 3. Формирование каталога всех известных студентов
        buildKnownStudentsRoster();

        // 4. Загрузка активной сессии
        try {
            const sessRaw = document.getElementById('server-session-data')?.textContent.trim();
            if (sessRaw && sessRaw !== '__SERVER_SESSION_JSON__') {
                activeSession = JSON.parse(sessRaw);
            }
        } catch (e) {}

        if (!activeSession) {
            try {
                const localSess = localStorage.getItem('activeExamSession');
                if (localSess) activeSession = JSON.parse(localSess);
            } catch(e) {}
        }

        updateKPIs();
        updateMistakesAnalytics();
        renderGroupsManager();
        renderDispatcherGroups();
        renderTable();

        rawServerResults = allResults.slice();
        rawServerGroups = allGroups.slice();

        const isDean = currentTeacher && (
            currentTeacher.role === 'dean' ||
            currentTeacher.username === 'dean_geo' ||
            currentTeacher.username === 'admin'
        );
        if (isDean) {
            initExecutiveDashboard();
        }

        if (activeSession) {
            checkActiveSessionState();
        }

        // Периодическая проверка активной сессии и обновление монитора
        setInterval(checkActiveSessionLoop, 2500);
    }

    function buildKnownStudentsRoster() {
        const map = {};
        allGroups.forEach(g => {
            (g.students || []).forEach(s => {
                const key = (s.email || s.name || '').trim().toLowerCase();
                if (key && !map[key]) {
                    map[key] = { name: s.name, email: s.email || '' };
                }
            });
        });
        allResults.forEach(r => {
            const email = (r.email || '').trim().toLowerCase();
            const name = r.name;
            if (email && email !== '-' && !map[email]) {
                map[email] = { name: name, email: email };
            }
        });
        allKnownStudents = Object.values(map);
    }

    function updateMistakesAnalytics() {
        const listEl = document.getElementById('mistakes-analytics-list');
        const badgeEl = document.getElementById('analytics-total-mistakes-badge');
        if (!listEl) return;

        const counts = {};
        let totalCount = 0;

        allResults.forEach(r => {
            const log = Array.isArray(r.mistakes_log) ? r.mistakes_log : [];
            log.forEach(item => {
                if (typeof item === 'string' && item.trim()) {
                    const name = item.trim();
                    counts[name] = (counts[name] || 0) + 1;
                    totalCount++;
                } else if (item && typeof item === 'object' && item.name) {
                    const name = String(item.name).trim();
                    counts[name] = (counts[name] || 0) + 1;
                    totalCount++;
                }
            });
        });

        if (badgeEl) {
            badgeEl.textContent = `Всего ошибок: ${totalCount}`;
        }

        const sortedEntries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
        const top5 = sortedEntries.slice(0, 5);

        if (top5.length === 0) {
            listEl.innerHTML = '<div class="analytics-empty-state">Нет зафиксированных ошибок в текущей выборке тестирований</div>';
            return;
        }

        const maxCount = top5[0][1] || 1;

        let html = '';
        top5.forEach(([objName, count], idx) => {
            const pct = Math.max(12, Math.round((count / maxCount) * 100));
            const rank = idx + 1;
            let badgeClass = 'badge-purple';
            if (rank === 1) badgeClass = 'badge-danger';
            else if (rank === 2) badgeClass = 'badge-warning';

            html += `
                <div class="mistake-item">
                    <div class="mistake-item-header">
                        <div class="mistake-item-name">
                            <span class="mistake-rank">#${rank}</span>
                            <strong>${escapeHtml(objName)}</strong>
                        </div>
                        <span class="badge ${badgeClass}">${count} ${getNoun(count, 'ошибка', 'ошибки', 'ошибок')}</span>
                    </div>
                    <div class="mistake-bar-track">
                        <div class="mistake-bar-fill rank-${rank}" style="width: ${pct}%;"></div>
                    </div>
                </div>
            `;
        });

        listEl.innerHTML = html;
    }

    function getNoun(number, one, two, five) {
        let n = Math.abs(number);
        n %= 100;
        if (n >= 5 && n <= 20) return five;
        n %= 10;
        if (n === 1) return one;
        if (n >= 2 && n <= 4) return two;
        return five;
    }

    function updateKPIs() {
        const total = allResults.length;
        const exams = allResults.filter(r => r.is_exam).length;
        const totalViolations = allResults.reduce((sum, r) => sum + (parseInt(r.violations) || 0), 0);
        const avgAcc = total > 0 ? Math.round(allResults.reduce((sum, r) => sum + (parseInt(r.accuracy) || 0), 0) / total) : 0;
        const violatingTests = allResults.filter(r => (parseInt(r.violations) || 0) > 0 || (r.exam_status && r.exam_status.includes('Подозрение'))).length;

        document.getElementById('kpi-total-tests').textContent = total;
        document.getElementById('kpi-exam-tests').textContent = exams;
        document.getElementById('kpi-avg-accuracy').textContent = `${avgAcc}%`;
        document.getElementById('kpi-total-violations').textContent = totalViolations;

        const vIcon = document.getElementById('kpi-violations-icon');
        if (vIcon) {
            if (totalViolations > 0) {
                vIcon.className = 'kpi-icon kpi-icon-red';
            } else {
                vIcon.className = 'kpi-icon kpi-icon-green';
                vIcon.textContent = '✓';
            }
        }

        document.getElementById('cnt-all').textContent = total;
        document.getElementById('cnt-exams').textContent = exams;
        document.getElementById('cnt-quizzes').textContent = total - exams;
        document.getElementById('cnt-violations').textContent = violatingTests;
        updateMistakesAnalytics();
    }

    // ==========================================
    // УПРАВЛЕНИЕ УЧЕБНЫМИ ГРУППАМИ (LMS GROUPS)
    // ==========================================
    function renderGroupsManager() {
        const container = document.getElementById('lms-groups-container');
        const countLabel = document.getElementById('groups-count-label');
        if (countLabel) countLabel.textContent = `${allGroups.length} групп`;
        if (!container) return;

        if (allGroups.length === 0) {
            container.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 24px; color: var(--text-muted);">
                    <div style="font-size: 28px; margin-bottom: 6px;">👥</div>
                    <strong>Нет созданных учебных групп</strong>
                    <div style="font-size: 12px; margin-top: 4px;">Нажмите кнопку «➕ Создать группу», чтобы добавить первый поток студентов.</div>
                </div>
            `;
            return;
        }

        let html = '';
        allGroups.forEach(grp => {
            const students = grp.students || [];
            const pillsHtml = students.length > 0 
                ? students.map(s => `<span class="student-pill"><span class="pill-dot"></span>${escapeHtml(s.name)}</span>`).join('')
                : '<span style="font-size: 11px; color: var(--text-muted);">Состав группы пуст</span>';

            html += `
                <div class="lms-group-card" id="card-${grp.id}">
                    <div class="lms-card-header">
                        <div class="lms-group-name">
                            <span>🎓</span>
                            <span>${escapeHtml(grp.name)}</span>
                        </div>
                        <div style="display: flex; gap: 4px;">
                            <button type="button" class="btn btn-secondary btn-sm" onclick="openEditGroupModal('${grp.id}')" title="Редактировать состав группы">
                                ✏️
                            </button>
                            <button type="button" class="btn btn-danger btn-sm" onclick="deleteGroup('${grp.id}')" title="Удалить группу">
                                🗑️
                            </button>
                        </div>
                    </div>

                    <div class="lms-group-desc">${escapeHtml(grp.description || 'Учебная академическая группа')}</div>

                    <div class="lms-roster-wrap">
                        <div class="lms-roster-header">
                            <span>Состав группы:</span>
                            <span>${students.length} студ.</span>
                        </div>
                        <div class="student-pills-list">
                            ${pillsHtml}
                        </div>
                    </div>

                    <div class="lms-card-actions">
                        <button type="button" class="btn btn-primary btn-sm btn-block" onclick="prepareTestForGroup('${grp.id}')">
                            <span>🚀</span> <span>Настроить тест для группы</span>
                        </button>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    function openCreateGroupModal() {
        document.getElementById('edit-group-id').value = '';
        document.getElementById('modal-group-name').value = '';
        document.getElementById('modal-group-desc').value = '';
        document.getElementById('lms-modal-title').textContent = 'Создание новой учебной группы';
        document.getElementById('btn-save-group').innerHTML = '<span>💾</span> <span>Сохранить группу</span>';

        renderModalStudentsChecklist([]);
        const modal = document.getElementById('lms-group-modal');
        if (modal) modal.style.display = 'flex';
    }

    function openEditGroupModal(groupId) {
        const grp = allGroups.find(g => g.id === groupId);
        if (!grp) return;

        document.getElementById('edit-group-id').value = grp.id;
        document.getElementById('modal-group-name').value = grp.name;
        document.getElementById('modal-group-desc').value = grp.description || '';
        document.getElementById('lms-modal-title').textContent = `Редактирование группы: ${grp.name}`;
        document.getElementById('btn-save-group').innerHTML = '<span>💾</span> <span>Обновить группу</span>';

        const selectedEmails = (grp.students || []).map(s => (s.email || s.name || '').trim().toLowerCase());
        renderModalStudentsChecklist(selectedEmails);

        const modal = document.getElementById('lms-group-modal');
        if (modal) modal.style.display = 'flex';
    }

    function closeGroupModal() {
        const modal = document.getElementById('lms-group-modal');
        if (modal) modal.style.display = 'none';
    }

    function renderModalStudentsChecklist(selectedEmails) {
        const container = document.getElementById('modal-students-checklist');
        if (!container) return;

        let html = '';
        allKnownStudents.forEach((st, idx) => {
            const key = (st.email || st.name || '').trim().toLowerCase();
            const isChecked = selectedEmails.includes(key);

            html += `
                <label class="student-check-item">
                    <input type="checkbox" class="student-checkbox" value="${escapeHtml(st.email)}" data-name="${escapeHtml(st.name)}" ${isChecked ? 'checked' : ''} onchange="updateCheckedStudentsCount()">
                    <div style="flex: 1;">
                        <strong style="color: #0F172A;">${escapeHtml(st.name)}</strong>
                        <div style="font-size: 11px; color: var(--text-muted);">${escapeHtml(st.email || '—')}</div>
                    </div>
                </label>
            `;
        });

        container.innerHTML = html;
        updateCheckedStudentsCount();
    }

    function updateCheckedStudentsCount() {
        const count = document.querySelectorAll('.student-checkbox:checked').length;
        const el = document.getElementById('checked-students-count');
        if (el) el.textContent = `Выбрано: ${count}`;
    }

    function addQuickStudentToList() {
        const nameInput = document.getElementById('quick-new-name');
        const emailInput = document.getElementById('quick-new-email');
        const name = (nameInput?.value || '').trim();
        const email = (emailInput?.value || '').trim().toLowerCase();

        if (!name) {
            alert('Пожалуйста, введите ФИО студента');
            return;
        }

        const newSt = { name: name, email: email || `${Date.now()}@sfedu.ru` };
        allKnownStudents.push(newSt);

        // Получаем текущие выбранные чекбоксы
        const currentChecked = Array.from(document.querySelectorAll('.student-checkbox:checked')).map(cb => (cb.value || cb.dataset.name).trim().toLowerCase());
        currentChecked.push((newSt.email || newSt.name).trim().toLowerCase());

        renderModalStudentsChecklist(currentChecked);

        if (nameInput) nameInput.value = '';
        if (emailInput) emailInput.value = '';
        showToast(`Студент ${name} добавлен в каталог`);
    }

    function saveGroupFromModal() {
        const idInput = document.getElementById('edit-group-id').value;
        const nameInput = document.getElementById('modal-group-name').value.trim();
        const descInput = document.getElementById('modal-group-desc').value.trim();

        if (!nameInput) {
            alert('Пожалуйста, укажите название учебной группы');
            return;
        }

        // Собираем отмеченных студентов
        const checkedBoxes = document.querySelectorAll('.student-checkbox:checked');
        const students = Array.from(checkedBoxes).map(cb => ({
            name: cb.dataset.name,
            email: cb.value
        }));

        let groupId = idInput;
        if (!groupId) {
            groupId = 'grp-' + Date.now();
        }

        const groupObj = {
            id: groupId,
            name: nameInput,
            description: descInput,
            students: students,
            created_at: new Date().toLocaleDateString('ru-RU') + ' ' + new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }),
            teacher_id: (currentTeacher && currentTeacher.teacher_id) ? currentTeacher.teacher_id : 'teacher-geo-01'
        };

        const existingIdx = allGroups.findIndex(g => g.id === groupId);
        if (existingIdx >= 0) {
            allGroups[existingIdx] = groupObj;
        } else {
            allGroups.push(groupObj);
        }

        // Сохраняем локально и отправляем на бэкенд
        localStorage.setItem('sfeduGroups', JSON.stringify(allGroups));

        fetch('/api/admin/groups', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(groupObj)
        }).catch(() => {});

        closeGroupModal();
        renderGroupsManager();
        renderDispatcherGroups();
        showToast(`Группа «${nameInput}» успешно сохранена!`);
    }

    function deleteGroup(groupId) {
        const grp = allGroups.find(g => g.id === groupId);
        if (!grp) return;

        if (confirm(`Вы действительно хотите удалить группу «${grp.name}»?`)) {
            allGroups = allGroups.filter(g => g.id !== groupId);
            localStorage.setItem('sfeduGroups', JSON.stringify(allGroups));

            fetch(`/api/admin/groups/${groupId}`, { method: 'DELETE' }).catch(() => {});

            renderGroupsManager();
            renderDispatcherGroups();
            showToast(`Группа «${grp.name}» удалена`);
        }
    }

    // ==========================================
    // КОНФИГУРАТОР СЕССИИ (TEST DISPATCHER)
    // ==========================================
    function renderDispatcherGroups() {
        const select = document.getElementById('dispatch-group-select');
        if (!select) return;

        let html = '';
        allGroups.forEach(grp => {
            const count = (grp.students || []).length;
            html += `<option value="${grp.id}">${escapeHtml(grp.name)} (${count} студ.)</option>`;
        });

        select.innerHTML = html;
    }

    function prepareTestForGroup(groupId) {
        const select = document.getElementById('dispatch-group-select');
        if (select) select.value = groupId;

        const sec = document.getElementById('test-dispatcher-section');
        if (sec) {
            sec.scrollIntoView({ behavior: 'smooth', block: 'center' });
            sec.style.outline = '3px solid #3B82F6';
            setTimeout(() => { sec.style.outline = 'none'; }, 1500);
        }
    }

    function handleDispatcherGroupChange() {}

    function launchGroupTest() {
        const groupId = document.getElementById('dispatch-group-select').value;
        const group = allGroups.find(g => g.id === groupId);

        if (!group) {
            alert('Пожалуйста, выберите учебную группу для запуска теста');
            return;
        }

        const mapUrl = document.getElementById('dispatch-region-select').value;
        const regionSelect = document.getElementById('dispatch-region-select');
        const regionName = regionSelect.options[regionSelect.selectedIndex].text;

        const quizType = document.getElementById('dispatch-type-select').value;
        const quizTypeSelect = document.getElementById('dispatch-type-select');
        const quizTypeName = quizTypeSelect.options[quizTypeSelect.selectedIndex].text;

        const questionCount = parseInt(document.getElementById('dispatch-count-select').value, 10);
        const timeLimitMinutes = parseInt(document.getElementById('dispatch-time-select').value, 10);

        const now = Date.now();
        const durationMs = timeLimitMinutes * 60 * 1000;

        activeSession = {
            sessionId: `SES-SFEDU-${Math.floor(Date.now() / 1000)}`,
            groupId: group.id,
            groupName: group.name,
            mapUrl: mapUrl,
            regionName: regionName,
            quizType: quizType,
            quizTypeName: quizTypeName,
            questionCount: questionCount,
            timeLimitMinutes: timeLimitMinutes,
            sessionStartedAt: now,
            durationMs: durationMs,
            endTime: now + durationMs,
            status: "active",
            students: group.students || [],
            teacher_id: (currentTeacher && currentTeacher.teacher_id) ? currentTeacher.teacher_id : 'teacher-geo-01'
        };

        // Сохранение в localStorage для мгновенного прототипа
        localStorage.setItem('activeExamSession', JSON.stringify(activeSession));

        // Отправка на бэкенд
        fetch('/api/exam/launch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                groupId: group.id,
                groupName: group.name,
                mapUrl: mapUrl,
                regionName: regionName,
                quizType: quizType,
                quizTypeName: quizTypeName,
                questionCount: questionCount,
                timeLimitMinutes: timeLimitMinutes,
                teacher_id: (currentTeacher && currentTeacher.teacher_id) ? currentTeacher.teacher_id : 'teacher-geo-01'
            })
        }).catch(() => {});

        checkActiveSessionState();
        showToast(`🚀 Синхронный тест запущен для группы «${group.name}»!`);

        const banner = document.getElementById('active-session-card');
        if (banner) banner.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // ==========================================
    // МОНИТОРИНГ АКТИВНОЙ СЕССИИ (LIVE MONITOR)
    // ==========================================
    function checkActiveSessionLoop() {
        if (!activeSession) {
            // Проверяем, не появилась ли активная сессия на сервере
            fetch('/api/exam/active-session')
                .then(r => r.json())
                .then(data => {
                    if (data && data.session && data.session.status === 'active') {
                        activeSession = data.session;
                        checkActiveSessionState();
                    }
                }).catch(() => {});
            return;
        }

        checkActiveSessionState();
    }

    function checkActiveSessionState() {
        const card = document.getElementById('active-session-card');
        if (!activeSession || activeSession.status !== 'active') {
            if (card) card.style.display = 'none';
            if (sessionCountdownTimer) clearInterval(sessionCountdownTimer);
            return;
        }

        if (card) card.style.display = 'block';

        const grpNameEl = document.getElementById('active-group-name');
        const regEl = document.getElementById('active-region-name');
        const testTypeEl = document.getElementById('active-test-type');
        const countEl = document.getElementById('active-count');
        const sessIdEl = document.getElementById('active-session-id');

        if (grpNameEl) grpNameEl.textContent = `Группа: ${activeSession.groupName}`;
        if (regEl) regEl.textContent = activeSession.regionName;
        if (testTypeEl) testTypeEl.textContent = activeSession.quizTypeName;
        if (countEl) countEl.textContent = `${activeSession.questionCount} вопросов`;
        if (sessIdEl) sessIdEl.textContent = activeSession.sessionId;

        updateSessionCountdown();
        if (!sessionCountdownTimer) {
            sessionCountdownTimer = setInterval(updateSessionCountdown, 1000);
        }

        updateActiveSessionStudentsRoster();
    }

    function updateSessionCountdown() {
        if (!activeSession) return;
        const now = Date.now();
        const endTime = activeSession.sessionStartedAt + activeSession.durationMs;
        const remainingSec = Math.max(0, Math.floor((endTime - now) / 1000));

        const mins = Math.floor(remainingSec / 60);
        const secs = remainingSec % 60;
        const timeStr = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

        const timerEl = document.getElementById('active-session-timer');
        if (timerEl) {
            timerEl.textContent = timeStr;
            timerEl.style.color = remainingSec < 120 ? '#EF4444' : '#38BDF8';
        }

        if (remainingSec <= 0) {
            activeSession.status = 'completed';
            localStorage.setItem('activeExamSession', JSON.stringify(activeSession));
            if (sessionCountdownTimer) {
                clearInterval(sessionCountdownTimer);
                sessionCountdownTimer = null;
            }
            showToast('⏰ Время синхронного тестирования истекло!');
            updateActiveSessionStudentsRoster();
        }
    }

    function updateActiveSessionStudentsRoster() {
        const tbody = document.getElementById('active-session-students-tbody');
        if (!tbody || !activeSession) return;

        const group = allGroups.find(g => g.id === activeSession.groupId) || { students: activeSession.students || [] };
        const students = group.students || [];

        let html = '';
        students.forEach((st, idx) => {
            // Ищем результаты студента по сессии или по ФИО в интервале сессии
            const submission = allResults.find(r => 
                (r.session_id === activeSession.sessionId || (r.name && r.name.toLowerCase() === st.name.toLowerCase())) &&
                (r.is_exam || r.group === activeSession.groupName)
            );

            let statusBadge = '';
            let scoreStr = '—';
            let violationsStr = '—';
            let tokenStr = '—';

            if (submission) {
                statusBadge = `<span class="status-badge status-green">✓ Сдано (${submission.accuracy}%)</span>`;
                scoreStr = `<b>${submission.score}</b> / ${submission.max_score}`;
                violationsStr = (submission.violations > 0)
                    ? `<span style="color:#EF4444; font-weight:700;">⚠️ ${submission.violations} уход(а)</span>`
                    : `<span style="color:#10B981; font-weight:700;">0 нарушений</span>`;
                tokenStr = submission.exam_token ? `<span class="token-badge">${submission.exam_token}</span>` : '—';
            } else if (activeSession.status === 'active') {
                statusBadge = `<span class="status-badge status-yellow">⏳ В процессе выполнения</span>`;
            } else {
                statusBadge = `<span class="status-badge status-red">❌ Не сдал (Время вышло)</span>`;
            }

            html += `
                <tr>
                    <td style="color:#94A3B8;">${idx + 1}</td>
                    <td><strong style="color:#FFFFFF;">${escapeHtml(st.name)}</strong></td>
                    <td style="color:#94A3B8;">${escapeHtml(st.email || '—')}</td>
                    <td>${statusBadge}</td>
                    <td>${scoreStr}</td>
                    <td>${violationsStr}</td>
                    <td>${tokenStr}</td>
                </tr>
            `;
        });

        tbody.innerHTML = html;
    }

    function stopCurrentSession() {
        if (!activeSession) return;
        if (confirm(`Принудительно остановить экзаменационную сессию для группы «${activeSession.groupName}»?`)) {
            activeSession.status = 'stopped';
            localStorage.setItem('activeExamSession', JSON.stringify(activeSession));

            fetch('/api/exam/stop', { method: 'POST' }).catch(() => {});

            if (sessionCountdownTimer) {
                clearInterval(sessionCountdownTimer);
                sessionCountdownTimer = null;
            }

            const card = document.getElementById('active-session-card');
            if (card) card.style.display = 'none';

            showToast('Сессия остановлена преподавателем');
        }
    }

    function copySessionStudentLink() {
        if (!activeSession) return;
        const link = `${window.location.origin}/${activeSession.mapUrl}?session_id=${activeSession.sessionId}&group=${encodeURIComponent(activeSession.groupName)}&start=${activeSession.sessionStartedAt}&time=${activeSession.timeLimitMinutes}&limit=${activeSession.questionCount}&mode=${activeSession.quizType}&region=${encodeURIComponent(activeSession.regionName || '')}`;
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(link).then(() => {
                showToast('Ссылка на тест скопирована в буфер!');
            }).catch(() => {
                prompt('Скопируйте ссылку для студентов:', link);
            });
        } else {
            prompt('Скопируйте ссылку для студентов:', link);
        }
    }

    // ==========================================
    // ФИЛЬТРАЦИЯ И ЖУРНАЛ РЕЗУЛЬТАТОВ
    // ==========================================
    function setFilter(filterType) {
        activeFilter = filterType;
        ['all', 'exams', 'quizzes', 'violations'].forEach(f => {
            const btn = document.getElementById(`filter-${f}`);
            if (btn) {
                btn.className = (f === filterType) ? (f === 'exams' ? 'pill-btn active-exam' : f === 'violations' ? 'pill-btn active-danger' : 'pill-btn active') : 'pill-btn';
            }
        });
        renderTable();
    }

    function handleSearchChange() {
        searchQuery = (document.getElementById('searchInput').value || '').trim().toLowerCase();
        renderTable();
    }

    function renderTable() {
        const tbody = document.getElementById('journalTableBody');
        const empty = document.getElementById('emptyPlaceholder');
        if (!tbody) return;

        let filtered = allResults.slice().reverse(); // recent first

        if (activeFilter === 'exams') {
            filtered = filtered.filter(r => r.is_exam);
        } else if (activeFilter === 'quizzes') {
            filtered = filtered.filter(r => !r.is_exam);
        } else if (activeFilter === 'violations') {
            filtered = filtered.filter(r => (parseInt(r.violations) || 0) > 0 || (r.exam_status && (r.exam_status.includes('Подозрение') || r.exam_status.includes('замечанием') || r.exam_status.includes('Аннулировано'))));
        }

        if (searchQuery) {
            filtered = filtered.filter(r => {
                const searchStr = `${r.name || ''} ${r.group || ''} ${r.email || ''} ${r.quiz_type || ''} ${r.exam_token || ''} ${r.exam_status || ''} ${r.session_id || ''}`.toLowerCase();
                return searchStr.includes(searchQuery);
            });
        }

        if (filtered.length === 0) {
            tbody.innerHTML = '';
            if (empty) empty.style.display = 'block';
            return;
        }

        if (empty) empty.style.display = 'none';

        let html = '';
        filtered.forEach(r => {
            const isExam = !!r.is_exam;
            const violations = parseInt(r.violations) || 0;
            const statusRaw = r.exam_status || (isExam ? 'Сдано' : 'Пройдено');

            let statusBadge = '';
            if (statusRaw.includes('Подозрение') || statusRaw.includes('Аннулировано') || violations >= 2) {
                statusBadge = `<span class="status-badge status-red" title="Зафиксировано ${violations} ухода со вкладки">🚨 Подозрение (${violations})</span>`;
            } else if (statusRaw.includes('Время истекло')) {
                statusBadge = `<span class="status-badge status-yellow">⏳ Время истекло</span>`;
            } else if (statusRaw.includes('Завершено досрочно')) {
                statusBadge = `<span class="status-badge status-yellow">⚠️ Завершено досрочно</span>`;
            } else if (statusRaw.includes('замечанием') || violations === 1) {
                statusBadge = `<span class="status-badge status-yellow" title="1 уход с вкладки">⚠️ Замечание (1)</span>`;
            } else {
                statusBadge = `<span class="status-badge status-green">✓ ${escapeHtml(statusRaw)}</span>`;
            }

            let modeBadge = `<span class="mode-badge mode-quiz">🎓 Викторина</span>`;
            if (isExam) {
                modeBadge = `<span class="mode-badge mode-exam">📝 Экзамен</span>`;
            } else if (r.quiz_type && r.quiz_type.includes('Пазл')) {
                modeBadge = `<span class="mode-badge" style="background:#ECFDF5; color:#059669; border:1px solid #A7F3D0;">🧩 Пазл</span>`;
            }

            let tokenHtml = '<span style="color: #94A3B8;">—</span>';
            if (r.exam_token && r.exam_token !== '-') {
                tokenHtml = `
                    <span class="token-badge">
                        <span>${escapeHtml(r.exam_token)}</span>
                        <span class="token-copy-icon" onclick="copyToken('${escapeHtml(r.exam_token)}')" title="Скопировать токен">📋</span>
                    </span>
                `;
            }

            const acc = parseInt(r.accuracy) || 0;
            const accClass = acc >= 65 ? 'acc-high' : acc >= 40 ? 'acc-mid' : 'acc-low';

            html += `
                <tr>
                    <td style="color: var(--text-muted); font-size: 12px;">${escapeHtml(r.date || '')}</td>
                    <td>
                        <div style="font-weight: 700; color: #0F172A;">${escapeHtml(r.name || 'Анонимно')}</div>
                        <div style="font-size: 11px; color: var(--text-muted);">${escapeHtml(r.email || '')}</div>
                    </td>
                    <td><span style="font-weight: 600; color: #334155;">${escapeHtml(r.group || '—')}</span></td>
                    <td><span style="color: #0369A1; font-weight: 600;">${escapeHtml(r.quiz_type || 'Общий')}</span></td>
                    <td>${modeBadge}</td>
                    <td>${statusBadge}</td>
                    <td>${tokenHtml}</td>
                    <td><b>${r.score}</b> / <span style="color: var(--text-muted);">${r.max_score}</span></td>
                    <td><span class="acc-pill ${accClass}">${acc}%</span></td>
                    <td style="color: var(--text-muted); font-size: 12px;">⏱ ${escapeHtml(r.time_spent || '—')}</td>
                </tr>
            `;
        });

        tbody.innerHTML = html;
    }

    function copyToken(token) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(token).then(() => {
                showToast(`Токен ${token} скопирован!`);
            }).catch(() => {
                prompt('Скопируйте токен:', token);
            });
        } else {
            prompt('Скопируйте токен:', token);
        }
    }

    function showToast(text) {
        const toast = document.getElementById('toast');
        const toastText = document.getElementById('toast-text');
        if (toast && toastText) {
            toastText.textContent = text;
            toast.style.display = 'flex';
            setTimeout(() => {
                toast.style.display = 'none';
            }, 2500);
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    window.addEventListener('DOMContentLoaded', initData);

    // ==========================================
    // ЛОГИКА DRAG-AND-DROP И ЗАГРУЗКИ КАРТ (ZIP)
    // ==========================================
    let selectedMapFile = null;
    let lastUploadedMapUrl = '';

    function initDropzoneEvents() {
        const dropzone = document.getElementById('map-dropzone');
        if (!dropzone) return;

        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove('dragover');
            });
        });

        dropzone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            if (dt && dt.files && dt.files.length > 0) {
                handleMapFileSelected(dt.files);
            }
        });
    }

    function handleMapFileSelected(files) {
        if (!files || files.length === 0) return;
        const file = files[0];
        if (!file.name.toLowerCase().endsWith('.zip')) {
            showToast('Пожалуйста, выберите архив в формате .zip', true);
            return;
        }

        selectedMapFile = file;
        const dropzoneTitle = document.getElementById('dropzone-title');
        const dropzoneSubtitle = document.getElementById('dropzone-subtitle');
        const dropzoneDisplay = document.getElementById('dropzone-file-display');
        const btnUpload = document.getElementById('btn-upload-map');

        if (dropzoneTitle) dropzoneTitle.style.display = 'none';
        if (dropzoneSubtitle) dropzoneSubtitle.style.display = 'none';

        if (dropzoneDisplay) {
            dropzoneDisplay.style.display = 'block';
            dropzoneDisplay.innerHTML = `
                <div class="dropzone-selected-file">
                    <span>📦 ${escapeHtml(file.name)}</span>
                    <span style="font-weight: 400; opacity: 0.8;">(${(file.size / (1024 * 1024)).toFixed(2)} МБ)</span>
                </div>
            `;
        }

        if (btnUpload) btnUpload.disabled = false;
        hideUploadFeedback();
    }

    function resetMapUploadForm() {
        selectedMapFile = null;
        lastUploadedMapUrl = '';
        const fileInput = document.getElementById('map-file-input');
        if (fileInput) fileInput.value = '';
        const nameInput = document.getElementById('upload-region-name');
        if (nameInput) nameInput.value = '';

        const dropzoneTitle = document.getElementById('dropzone-title');
        const dropzoneSubtitle = document.getElementById('dropzone-subtitle');
        const dropzoneDisplay = document.getElementById('dropzone-file-display');
        const btnUpload = document.getElementById('btn-upload-map');

        if (dropzoneTitle) dropzoneTitle.style.display = 'block';
        if (dropzoneSubtitle) dropzoneSubtitle.style.display = 'block';
        if (dropzoneDisplay) {
            dropzoneDisplay.style.display = 'none';
            dropzoneDisplay.innerHTML = '';
        }
        if (btnUpload) btnUpload.disabled = true;

        hideUploadFeedback();
    }

    function hideUploadFeedback() {
        const progressBox = document.getElementById('upload-progress-box');
        const successBox = document.getElementById('upload-success-box');
        const errorBox = document.getElementById('upload-error-box');
        if (progressBox) progressBox.style.display = 'none';
        if (successBox) successBox.style.display = 'none';
        if (errorBox) errorBox.style.display = 'none';
    }

    async function handleMapUploadSubmit(event) {
        event.preventDefault();
        if (!selectedMapFile) {
            showToast('Выберите ZIP-файл перед загрузкой', true);
            return;
        }

        const regionName = (document.getElementById('upload-region-name').value || '').trim();
        const progressBox = document.getElementById('upload-progress-box');
        const progressBar = document.getElementById('upload-progress-bar');
        const progressStatus = document.getElementById('upload-status-text');
        const progressPercent = document.getElementById('upload-percent-text');
        const successBox = document.getElementById('upload-success-box');
        const errorBox = document.getElementById('upload-error-box');
        const btnUpload = document.getElementById('btn-upload-map');

        hideUploadFeedback();
        if (btnUpload) btnUpload.disabled = true;
        if (progressBox) progressBox.style.display = 'block';

        let progress = 10;
        if (progressBar) progressBar.style.width = '10%';
        if (progressPercent) progressPercent.textContent = '10%';
        if (progressStatus) progressStatus.textContent = '⏳ Передача ZIP-архива на сервер...';

        const timer = setInterval(() => {
            if (progress < 85) {
                progress += Math.floor(Math.random() * 15) + 5;
                if (progress > 85) progress = 85;
                if (progressBar) progressBar.style.width = `${progress}%`;
                if (progressPercent) progressPercent.textContent = `${progress}%`;
                if (progress > 40 && progress < 70) {
                    if (progressStatus) progressStatus.textContent = '🔍 Распаковка и анализ Shapefile геометрии...';
                } else if (progress >= 70) {
                    if (progressStatus) progressStatus.textContent = '🗺️ Генерация Leaflet слоев и топологии районов...';
                }
            }
        }, 400);

        const formData = new FormData();
        formData.append('file', selectedMapFile);
        if (regionName) {
            formData.append('region_name', regionName);
        }

        try {
            const res = await fetch('/api/upload-map', {
                method: 'POST',
                body: formData
            });

            clearInterval(timer);

            if (!res.ok) {
                let errText = 'Ошибка при обработке архива';
                try {
                    const errJson = await res.json();
                    errText = errJson.detail || errJson.message || errText;
                } catch(e) {}
                throw new Error(errText);
            }

            const data = await res.json();
            if (progressBar) progressBar.style.width = '100%';
            if (progressPercent) progressPercent.textContent = '100%';
            if (progressStatus) progressStatus.textContent = '✅ Карта успешно создана!';

            setTimeout(() => {
                if (progressBox) progressBox.style.display = 'none';
                if (successBox) successBox.style.display = 'block';

                const titleEl = document.getElementById('upload-success-title');
                const descEl = document.getElementById('upload-success-desc');
                const linkEl = document.getElementById('upload-result-link');

                if (titleEl) titleEl.textContent = `Карта «${data.region_name}» готова!`;
                if (descEl) descEl.textContent = `Сформировано ${data.districts_count || 0} полигонов территорий. Карта сохранена в public/maps/${data.filename}`;
                if (linkEl) {
                    linkEl.href = data.map_url || data.direct_url;
                    lastUploadedMapUrl = data.map_url || data.direct_url;
                }

                // Добавляем созданную карту в выпадающий список тестирования
                const dispatchSelect = document.getElementById('dispatch-region-select');
                if (dispatchSelect && data.filename) {
                    const opt = document.createElement('option');
                    opt.value = data.filename;
                    opt.textContent = `🗺️ ${data.region_name} (Загруженная карта)`;
                    opt.selected = true;
                    dispatchSelect.insertBefore(opt, dispatchSelect.firstChild);
                }

                showToast(`Карта «${data.region_name}» сгенерирована!`);
                loadMapsList();
            }, 600);

        } catch (err) {
            clearInterval(timer);
            if (progressBox) progressBox.style.display = 'none';
            if (errorBox) errorBox.style.display = 'block';
            const msgEl = document.getElementById('upload-error-message');
            if (msgEl) msgEl.textContent = err.message || 'Произошла непредвиденная ошибка';
            showToast('Ошибка при загрузке карты', true);
        } finally {
            if (btnUpload) btnUpload.disabled = false;
        }
    }

    function copyUploadedMapLink() {
        if (!lastUploadedMapUrl) return;
        const fullUrl = `${window.location.origin}${lastUploadedMapUrl.startsWith('/') ? '' : '/'}${lastUploadedMapUrl}`;
        navigator.clipboard.writeText(fullUrl).then(() => {
            showToast('Ссылка на карту скопирована в буфер обмена!');
        }).catch(() => {
            showToast('Не удалось скопировать ссылку', true);
        });
    }

    window.addEventListener('DOMContentLoaded', initDropzoneEvents);


    // ==========================================
    // УПРАВЛЕНИЕ КАРТАМИ (CRUD)
    // ==========================================
    async function loadMapsList() {
        const tbody = document.getElementById('maps-table-body');
        const emptyBox = document.getElementById('maps-empty-placeholder');
        const counterBadge = document.getElementById('maps-counter-badge');
        if (!tbody) return;

        try {
            const res = await fetch('/api/maps');
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const maps = await res.json();

            if (counterBadge) {
                counterBadge.textContent = `${maps.length} ${getMapWordEnding(maps.length)}`;
            }

            if (!maps || maps.length === 0) {
                tbody.innerHTML = '';
                if (emptyBox) emptyBox.style.display = 'block';
                return;
            }

            if (emptyBox) emptyBox.style.display = 'none';

            tbody.innerHTML = maps.map(m => {
                const safeName = escapeHtml(m.filename || m.name);
                const sizeStr = escapeHtml(m.size_formatted || `${m.size} Б`);
                const dateStr = escapeHtml(m.created_at || m.date || '—');
                const mapUrl = m.url || `/public/maps/${encodeURIComponent(m.filename || m.name)}`;

                return `
                    <tr>
                        <td>
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="font-size: 20px;">🗺️</span>
                                <div>
                                    <div style="font-weight: 700; color: #0F172A;">${safeName}</div>
                                    <div style="font-size: 11px; color: #64748B;">public/maps/${safeName}</div>
                                </div>
                            </div>
                        </td>
                        <td>
                            <span style="font-size: 12px; font-weight: 600; color: #334155; background: #F1F5F9; padding: 3px 8px; border-radius: 6px; border: 1px solid #E2E8F0;">
                                ${sizeStr}
                            </span>
                        </td>
                        <td>
                            <span style="font-size: 12px; color: #475569;">
                                ${dateStr}
                            </span>
                        </td>
                        <td style="text-align: right;">
                            <div style="display: flex; gap: 8px; justify-content: flex-end; align-items: center;">
                                <a href="${mapUrl}" target="_blank" class="btn btn-secondary btn-sm" title="Открыть карту в новой вкладке">
                                    <span>↗️</span> <span>Открыть</span>
                                </a>
                                <button type="button" class="btn btn-danger btn-sm" onclick="deleteMap('${safeName}')" title="Удалить файл карты">
                                    <span>🗑️</span> <span>Удалить</span>
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');
        } catch (e) {
            console.error('Ошибка загрузки списка карт:', e);
            if (tbody) {
                tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: #EF4444; padding: 18px;">⚠️ Не удалось загрузить список карт</td></tr>`;
            }
        }
    }

    async function deleteMap(filename) {
        if (!filename) return;
        const confirmed = window.confirm(`Вы уверены, что хотите удалить карту «${filename}»?\n\nФайл будет безвозвратно удален с сервера.`);
        if (!confirmed) return;

        try {
            const res = await fetch(`/api/maps/${encodeURIComponent(filename)}`, {
                method: 'DELETE'
            });

            if (res.ok) {
                const data = await res.json().catch(() => ({}));
                showToast(data.message || `Карта «${filename}» успешно удалена`);
                loadMapsList();
            } else {
                const err = await res.json().catch(() => ({}));
                showToast(err.detail || 'Не удалось удалить карту', true);
            }
        } catch (e) {
            showToast('Сетевая ошибка при удалении карты', true);
        }
    }

    function getMapWordEnding(count) {
        const rem10 = count % 10;
        const rem100 = count % 100;
        if (rem100 >= 11 && rem100 <= 19) return 'карт';
        if (rem10 === 1) return 'карта';
        if (rem10 >= 2 && rem10 <= 4) return 'карты';
        return 'карт';
    }

    window.addEventListener('DOMContentLoaded', loadMapsList);


    // ==========================================
    // 🏛️ EXECUTIVE DASHBOARD (ДЕКАНАТ ЮФУ)
    // ==========================================
    function initExecutiveDashboard() {
        const section = document.getElementById('executive-dashboard-section');
        if (section) section.style.display = 'block';

        const filterSelect = document.getElementById('executive-teacher-filter');
        if (filterSelect && allTeachers.length > 0) {
            const seen = new Set();
            filterSelect.innerHTML = '<option value="all">🌐 Сводка по всем преподавателям (ЮФУ)</option>';
            allTeachers.forEach(t => {
                if (t.role !== 'dean' && !seen.has(t.teacher_id)) {
                    seen.add(t.teacher_id);
                    const opt = document.createElement('option');
                    opt.value = t.teacher_id;
                    opt.textContent = `👨‍🏫 ${t.full_name} (${t.department || t.organization || 'Кафедра'})`;
                    filterSelect.appendChild(opt);
                }
            });
        }
        updateExecutiveMetrics();
    }

    function updateExecutiveMetrics() {
        const deptsEl = document.getElementById('exec-metric-depts');
        const teachersEl = document.getElementById('exec-metric-teachers');
        const avgScoreEl = document.getElementById('exec-metric-avg-score');
        const integrityEl = document.getElementById('exec-metric-integrity');

        const uniqueDepts = new Set();
        const uniqueTeachers = new Set();
        allTeachers.forEach(t => {
            if (t.department) uniqueDepts.add(t.department);
            if (t.role !== 'dean') uniqueTeachers.add(t.teacher_id);
        });

        if (deptsEl) deptsEl.textContent = `${uniqueDepts.size || 2} кафедры`;
        if (teachersEl) teachersEl.textContent = `${uniqueTeachers.size || 2} преподавателя`;

        const total = allResults.length;
        if (total > 0) {
            const avgAcc = Math.round(allResults.reduce((sum, r) => sum + (r.accuracy || 0), 0) / total);
            if (avgScoreEl) avgScoreEl.textContent = `${avgAcc}%`;

            const violationsCount = allResults.reduce((sum, r) => sum + (r.violations || 0), 0);
            const integrityPct = Math.max(70, Math.min(100, Math.round(100 - (violationsCount / total) * 15)));
            if (integrityEl) integrityEl.textContent = `${integrityPct}%`;
        }
    }

    function onExecutiveTeacherFilterChange(teacherId) {
        if (teacherId === 'all') {
            allResults = rawServerResults.slice();
            allGroups = rawServerGroups.slice();
        } else {
            allResults = rawServerResults.filter(r => (r.teacher_id || 'teacher-ivanov') === teacherId);
            allGroups = rawServerGroups.filter(g => (g.teacher_id || 'teacher-ivanov') === teacherId);
        }

        buildKnownStudentsRoster();
        updateKPIs();
        updateMistakesAnalytics();
        renderGroupsManager();
        renderDispatcherGroups();
        renderTable();
        updateExecutiveMetrics();
        showToast(teacherId === 'all' ? 'Показана сводка по всему факультету' : 'Применен фильтр преподавателя');
    }
    window.onExecutiveTeacherFilterChange = onExecutiveTeacherFilterChange;

    // ==========================================
    // 📄 ГЕНЕРАЦИЯ EXECUTIVE PDF-ОТЧЕТА (html2pdf)
    // ==========================================
    function generateExecutivePDFReport() {
        if (typeof html2pdf === 'undefined') {
            alert('Библиотека html2pdf.js еще инициализируется. Пожалуйста, повторите попытку через 2 секунды.');
            return;
        }

        showToast('⏳ Формирование официального PDF-отчета...');

        const dateStr = new Date().toLocaleDateString('ru-RU') + ' ' + new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
        const teacherName = currentTeacher ? currentTeacher.full_name : 'Преподаватель ЮФУ';
        const orgName = currentTeacher ? currentTeacher.organization : 'Институт наук о Земле ЮФУ';
        const deptName = currentTeacher ? (currentTeacher.department || 'Геолого-географический факультет') : 'Кафедра физической географии';
        const isDean = currentTeacher && (currentTeacher.role === 'dean' || currentTeacher.username === 'dean_geo' || currentTeacher.username === 'admin');

        // Подсчет ключевых метрик для отчета
        const totalTests = allResults.length;
        const examTests = allResults.filter(r => r.is_exam).length;
        const avgAcc = totalTests > 0 ? Math.round(allResults.reduce((s, r) => s + (r.accuracy || 0), 0) / totalTests) : 0;
        const totalViolations = allResults.reduce((s, r) => s + (r.violations || 0), 0);

        // Формирование строк таблицы результатов
        let tableRowsHtml = '';
        allResults.slice(0, 35).forEach((r, idx) => {
            const statusClass = r.is_exam ? (r.violations > 0 ? '#DC2626' : '#10B981') : '#2563EB';
            tableRowsHtml += `
                <tr style="border-bottom: 1px solid #E5E7EB; font-size: 11px;">
                    <td style="padding: 6px 8px; text-align: center;">${idx + 1}</td>
                    <td style="padding: 6px 8px;"><strong>${escapeHtml(r.name || 'Анонимно')}</strong></td>
                    <td style="padding: 6px 8px;">${escapeHtml(r.group || '-')}</td>
                    <td style="padding: 6px 8px;">${escapeHtml(r.quiz_type || 'Общий')}</td>
                    <td style="padding: 6px 8px; text-align: center; color: ${statusClass}; font-weight: bold;">${escapeHtml(r.exam_status || (r.is_exam ? 'Сдано' : 'Пройдено'))}</td>
                    <td style="padding: 6px 8px; text-align: center; font-weight: bold;">${r.score} / ${r.max_score}</td>
                    <td style="padding: 6px 8px; text-align: center; font-weight: bold; color: ${r.accuracy >= 70 ? '#059669' : '#DC2626'};">${r.accuracy}%</td>
                    <td style="padding: 6px 8px; text-align: center;">${r.violations || 0}</td>
                    <td style="padding: 6px 8px; text-align: center; color: #6B7280;">${r.date || '-'}</td>
                </tr>
            `;
        });

        // Создаем временный чистый DOM-элемент строгого академического стиля
        const reportEl = document.createElement('div');
        reportEl.id = 'executive-pdf-container';
        reportEl.style.width = '1000px';
        reportEl.style.padding = '30px 40px';
        reportEl.style.background = '#FFFFFF';
        reportEl.style.color = '#111827';
        reportEl.style.fontFamily = 'Arial, "Segoe UI", sans-serif';

        reportEl.innerHTML = `
            <div style="border-bottom: 3px solid #1E3A8A; padding-bottom: 15px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 15px;">
                    <div style="font-size: 38px;">🎓</div>
                    <div>
                        <div style="font-size: 14px; font-weight: bold; color: #1E3A8A; text-transform: uppercase; letter-spacing: 0.5px;">Министерство науки и высшего образования РФ</div>
                        <div style="font-size: 18px; font-weight: 800; color: #0F172A;">ЮЖНЫЙ ФЕДЕРАЛЬНЫЙ УНИВЕРСИТЕТ</div>
                        <div style="font-size: 13px; color: #4B5563;">${escapeHtml(orgName)} • ${escapeHtml(deptName)}</div>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="display: inline-block; background: #EEF2FF; color: #3730A3; font-weight: bold; font-size: 11px; padding: 4px 10px; border-radius: 6px; border: 1px solid #C7D2FE;">
                        ${isDean ? 'EXECUTIVE SUMMARY (ДЕКАНАТ)' : 'АТТЕСТАЦИОННАЯ ВЕДОМОСТЬ'}
                    </div>
                    <div style="font-size: 11px; color: #6B7280; margin-top: 5px;">Дата: ${dateStr}</div>
                </div>
            </div>

            <div style="margin-bottom: 20px;">
                <h2 style="font-size: 18px; font-weight: 800; margin: 0 0 5px 0; color: #0F172A; text-align: center; text-transform: uppercase;">
                    Сводный отчет академической успеваемости в системе GeoAtlas
                </h2>
                <div style="font-size: 12px; color: #6B7280; text-align: center;">
                    Ответственное лицо: <strong>${escapeHtml(teacherName)}</strong> • Режим: <strong>${isDean ? 'Сводка по всем кафедрам' : 'Кафедральная ведомость'}</strong>
                </div>
            </div>

            <!-- KPI Cards -->
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 25px;">
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; text-align: center;">
                    <div style="font-size: 11px; color: #64748B;">Всего попыток сдачи</div>
                    <div style="font-size: 20px; font-weight: 800; color: #0284C7; margin-top: 3px;">${totalTests}</div>
                </div>
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; text-align: center;">
                    <div style="font-size: 11px; color: #64748B;">Контрольных срезов</div>
                    <div style="font-size: 20px; font-weight: 800; color: #7C3AED; margin-top: 3px;">${examTests}</div>
                </div>
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; text-align: center;">
                    <div style="font-size: 11px; color: #64748B;">Средняя успеваемость</div>
                    <div style="font-size: 20px; font-weight: 800; color: #059669; margin-top: 3px;">${avgAcc}%</div>
                </div>
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; text-align: center;">
                    <div style="font-size: 11px; color: #64748B;">Нарушений Anti-Cheat</div>
                    <div style="font-size: 20px; font-weight: 800; color: ${totalViolations > 0 ? '#DC2626' : '#10B981'}; margin-top: 3px;">${totalViolations}</div>
                </div>
            </div>

            <!-- Table -->
            <div style="margin-bottom: 30px;">
                <div style="font-size: 13px; font-weight: 700; color: #1E293B; margin-bottom: 8px; text-transform: uppercase;">
                    Ведомость контрольных и проверочных работ
                </div>
                <table style="width: 100%; border-collapse: collapse; border: 1px solid #CBD5E1; background: #FFFFFF;">
                    <thead>
                        <tr style="background: #F1F5F9; font-size: 11px; color: #475569; text-transform: uppercase; border-bottom: 2px solid #CBD5E1;">
                            <th style="padding: 8px; text-align: center; width: 30px;">№</th>
                            <th style="padding: 8px; text-align: left;">Студент</th>
                            <th style="padding: 8px; text-align: left;">Группа</th>
                            <th style="padding: 8px; text-align: left;">Тема</th>
                            <th style="padding: 8px; text-align: center;">Статус</th>
                            <th style="padding: 8px; text-align: center;">Баллы</th>
                            <th style="padding: 8px; text-align: center;">Успех</th>
                            <th style="padding: 8px; text-align: center;">Фокус</th>
                            <th style="padding: 8px; text-align: center;">Дата</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${tableRowsHtml || '<tr><td colspan="9" style="text-align: center; padding: 20px; color: #9CA3AF;">Нет данных</td></tr>'}
                    </tbody>
                </table>
            </div>

            <!-- Signatures Footer -->
            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-top: 40px; padding-top: 20px; border-top: 2px dashed #E2E8F0;">
                <div>
                    <div style="font-size: 11px; color: #64748B;">Электронный идентификатор отчета: SFEDU-EXECUTIVE-${Date.now()}</div>
                    <div style="font-size: 10px; color: #94A3B8; margin-top: 2px;">Сформировано автоматически интерактивным геоатласом GeoAtlas SaaS</div>
                </div>
                <div style="display: flex; gap: 40px;">
                    <div style="text-align: center;">
                        <div style="width: 180px; border-bottom: 1px solid #000; height: 30px;"></div>
                        <div style="font-size: 11px; color: #475569; margin-top: 4px;">Преподаватель (подпись)</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="width: 180px; border-bottom: 1px solid #000; height: 30px;"></div>
                        <div style="font-size: 11px; color: #475569; margin-top: 4px;">Деканат / М.П.</div>
                    </div>
                </div>
            </div>
        `;

        // Временно добавляем в DOM вне зоны видимости для генерации
        reportEl.style.position = 'fixed';
        reportEl.style.left = '-9999px';
        reportEl.style.top = '0';
        document.body.appendChild(reportEl);

        const opt = {
            margin: [8, 8, 8, 8],
            filename: 'Report_GeoAtlas.pdf',
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2, useCORS: true, logging: false },
            jsPDF: { unit: 'mm', format: 'a4', orientation: 'landscape' }
        };

        html2pdf().set(opt).from(reportEl).save().then(() => {
            document.body.removeChild(reportEl);
            showToast('✅ Отчет Report_GeoAtlas.pdf успешно скачан!');
        }).catch(err => {
            console.error('PDF generation error:', err);
            document.body.removeChild(reportEl);
            alert('Ошибка при генерации PDF: ' + err.message);
        });
    }
    window.generateExecutivePDFReport = generateExecutivePDFReport;
