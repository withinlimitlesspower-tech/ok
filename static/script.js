// Vanilla JavaScript for Task Manager frontend

const API_BASE = '';  // Same origin

// DOM Elements
const taskList = document.getElementById('task-list');
const addTaskForm = document.getElementById('add-task-form');
const filterSelect = document.getElementById('filter');
const editModal = document.getElementById('edit-modal');
const closeEditModal = document.getElementById('close-edit-modal');
const editForm = document.getElementById('edit-task-form');
const editIdInput = document.getElementById('edit-task-id');
const editTitleInput = document.getElementById('edit-task-title');
const editDescInput = document.getElementById('edit-task-description');
const editCompletedCheckbox = document.getElementById('edit-task-completed');

// Load tasks on page load and when filter changes
document.addEventListener('DOMContentLoaded', loadTasks);
filterSelect.addEventListener('change', loadTasks);

// Add new task
addTaskForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = document.getElementById('task-title').value.trim();
    const description = document.getElementById('task-description').value.trim();
    if (!title) return;

    try {
        const res = await fetch(`${API_BASE}/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, description: description || null })
        });
        if (!res.ok) {
            const errData = await res.json();
            alert(`Error: ${errData.detail || 'Failed to create task'}`);
            return;
        }
        addTaskForm.reset();
        loadTasks();
    } catch (err) {
        console.error(err);
        alert('Network error: Unable to create task.');
    }
});

// Load tasks with optional filter
async function loadTasks() {
    const filter = filterSelect.value;
    let url = `${API_BASE}/tasks`;
    if (filter === 'active') url += '?completed=false';
    else if (filter === 'completed') url += '?completed=true';
    
    try {
        const res = await fetch(url);
        if (!res.ok) {
            const errData = await res.json();
            alert(`Error: ${errData.detail || 'Failed to load tasks'}`);
            return;
        }
        const tasks = await res.json();
        renderTasks(tasks);
    } catch (err) {
        console.error(err);
        alert('Network error: Unable to load tasks.');
    }
}

// Render tasks to DOM
function renderTasks(tasks) {
    taskList.innerHTML = '';
    if (tasks.length === 0) {
        taskList.innerHTML = '<p style="text-align:center; color:#888; margin-top:2rem;">No tasks found. Add one!</p>';
        return;
    }

    tasks.forEach(task => {
        const card = document.createElement('div');
        card.className = `task-card ${task.completed ? 'completed' : ''}`;
        card.dataset.id = task.id;

        const infoDiv = document.createElement('div');
        infoDiv.className = 'task-info';

        const titleEl = document.createElement('div');
        titleEl.className = 'task-title';
        titleEl.textContent = task.title;

        const descEl = document.createElement('div');
        descEl.className = 'task-description';
        descEl.textContent = task.description || '';

        infoDiv.appendChild(titleEl);
        if (task.description) infoDiv.appendChild(descEl);

        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'task-actions';

        const editBtn = document.createElement('button');
        editBtn.className = 'edit-btn';
        editBtn.textContent = 'Edit';
        editBtn.addEventListener('click', () => openEditModal(task));

        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'delete-btn';
        deleteBtn.textContent = 'Delete';
        deleteBtn.addEventListener('click', () => deleteTask(task.id));

        actionsDiv.appendChild(editBtn);
        actionsDiv.appendChild(deleteBtn);

        card.appendChild(infoDiv);
        card.appendChild(actionsDiv);
        taskList.appendChild(card);
    });
}

// Open edit modal with pre-filled data
function openEditModal(task) {
    editIdInput.value = task.id;
    editTitleInput.value = task.title;
    editDescInput.value = task.description || '';
    editCompletedCheckbox.checked = task.completed;
    editModal.classList.add('active');
}

// Close edit modal
closeEditModal.addEventListener('click', () => {
    editModal.classList.remove('active');
});

// Close modal if clicking outside
window.addEventListener('click', (e) => {
    if (e.target === editModal) {
        editModal.classList.remove('active');
    }
});

// Update task when edit form submitted
editForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const id = parseInt(editIdInput.value);
    const title = editTitleInput.value.trim();
    const description = editDescInput.value.trim();
    const completed = editCompletedCheckbox.checked;

    if (!title) return;

    try {
        const res = await fetch(`${API_BASE}/tasks/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title,
                description: description || null,
                completed
            })
        });
        if (!res.ok) {
            const errData = await res.json();
            alert(`Error: ${errData.detail || 'Failed to update task'}`);
            return;
        }
        editModal.classList.remove('active');
        loadTasks();
    } catch (err) {
        console.error(err);
        alert('Network error: Unable to update task.');
    }
});

// Delete a task
async function deleteTask(id) {
    if (!confirm('Are you sure you want to delete this task?')) return;
    
    try {
        const res = await fetch(`${API_BASE}/tasks/${id}`, { method: 'DELETE' });
        if (!res.ok) {
            const errData = await res.json();
            alert(`Error: ${errData.detail || 'Failed to delete task'}`);
            return;
        }
        loadTasks();
    } catch (err) {
        console.error(err);
        alert('Network error: Unable to delete task.');
    }
}
