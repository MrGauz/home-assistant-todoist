// Todoist Project Card

const INPUT_TEXT_ENTITY_ID = 'input_text.todoist_closed_task';
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

class TodoistCard extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({
            mode: 'open'
        });
    }

    /* This is called every time sensor is updated */
    set hass(hass) {
        const config = this.config;
        const maxEntries = config.max_entries || 10;
        const showProjectName = config.show_project_name || true;
        const entityIds = config.entity ? [config.entity] : config.entities || [];

        const root = this.shadowRoot.getElementById('container');
        root.innerHTML = '';

        for (const entityId of entityIds) {
            const entity = hass.states[entityId];
            if (!entity) {
                throw new Error("Entity State Unavailable");
            }

            if (showProjectName) {
                const projectName = document.createElement('div');
                projectName.className = 'project';
                projectName.innerText = entity.attributes.friendly_name;

                if (entity.attributes.project_url) {
                    projectName.addEventListener('click', function () {
                        window.open(entity.attributes.project_url, '_blank').focus();
                    });
                }

                root.appendChild(projectName);
            }

            const tasks = document.createElement('ul');
            tasks.className = 'tasks';
            tasks.id = 'todoist-tasks-' + entityId;

            entity.attributes.tasks.slice(0, maxEntries).forEach(apiTask => {
                let dueToText = '';
                if (apiTask.due && apiTask.due.date) {
                    // Parse due date
                    let parsedDate = new Date(apiTask.due.date);
                    dueToText += parsedDate.getDate() + ' ' + MONTHS[parsedDate.getMonth()];
                }
                if (apiTask.due && apiTask.due.datetime != null) {
                    // Parse due time
                    let parsedTime = new Date(apiTask.due.datetime);
                    dueToText += ' ' + parsedTime.getHours() + ':' + parsedTime.getMinutes().toString().padStart(2, '0');
                }

                const task = document.createElement('li');
                task.id = apiTask.id;
                task.classList.add('task');
                if (hass.states[INPUT_TEXT_ENTITY_ID].state
                    && apiTask.id === hass.states[INPUT_TEXT_ENTITY_ID].state.split(':')[1]) {
                    task.classList.add('checked');
                }
                const taskInner = document.createElement('div');

                const text = document.createElement('div');
                text.innerText = apiTask.content;
                taskInner.appendChild(text);

                if (dueToText) {
                    const dueTo = document.createElement('div');
                    dueTo.className = 'due-date';
                    dueTo.innerText = dueToText;
                    taskInner.appendChild(dueTo);
                }

                task.appendChild(taskInner);

                task.addEventListener('click', event => {
                    const task = event.target.closest('.task');
                    if (task && !task.classList.contains('checked')) {
                        // Disallow unselecting a task ^
                        hass.callService("input_text", "set_value", {
                            entity_id: INPUT_TEXT_ENTITY_ID,
                            value: `${entityId}:${task.id}`
                        });
                    }
                }, false);

                tasks.appendChild(task);
            });

            root.appendChild(tasks);
        }
    }

    /* This is called only when config is updated */
    setConfig(config) {
        const root = this.shadowRoot;
        if (root.lastChild) root.removeChild(root.lastChild);

        this.config = config;

        const card = document.createElement('ha-card');
        const content = document.createElement('div');
        const style = document.createElement('style');

        style.textContent = `
            * {
              box-sizing: border-box;
            }

            .container {
                padding: 10px;
                line-height: 1.5em;
            }

            .project {
                opacity: 0.8;
                font-weight: 500;
                font-size: 150%;
                width: 100%;
                text-align: left;
                padding: 10px 10px 5px 5px;
            }

            .tasks {
                width: 100%;
                font-weight: 400;
                font-size:120%;
                line-height: 1.5em;
                padding-bottom: 20px;
                padding-inline-start: 20px;
                padding-inline-end: 20px;
            }

            ul li {
                cursor: pointer;
                position: relative;
                padding: 12px 8px 12px 40px;
                transition: 0.2s;

                /* make the list items unselectable */
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
                user-select: none;
            }

            ul li:nth-child(odd) {
                background: #292929;
            }

            ul li:hover {
                background: #3B3B3B;
            }

            ul li.checked {
                background: #595959;
                color: #424242;
                text-decoration: line-through;
            }

            ul li::before {
                content: '';
                position: absolute;
                border-color: #fff;
                border-style: solid;
                border-width: 2px;
                border-radius: 50%;
                top: 14px;
                left: 16px;
                height: 10px;
                width: 10px;
            }

            ul li.checked::before {
                content: '';
                position: absolute;
                border-color: #fff;
                border-style: solid;
                border-width: 0 2px 2px 0;
                border-radius: 0;
                top: 10px;
                left: 16px;
                transform: rotate(45deg);
                height: 15px;
                width: 7px;
            }

            .task {
                padding-top: 10px;
                display: flex;
                flex-direction: row;
                flex-wrap: nowrap;
                align-items: flex-start;
                gap: 20px;
                line-height: 1.2em;
            }

            .due-date {
                font-size: 75%;
                opacity: 0.7;
            }
        `;

        content.id = "container";
        content.className = "container";
        card.header = config.title;
        card.appendChild(style);
        card.appendChild(content);

        root.appendChild(card);
    }

    // The height of the card.
    getCardSize() {
        return 5;
    }
}

customElements.define('todoist-card', TodoistCard);