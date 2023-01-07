// Todoist Project Card

const INPUT_TEXT_ENTITY_ID = 'input_text.todoist_closed_tasks';
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

        let content = "";

        for (const entityId of entityIds) {
            const entity = hass.states[entityId];
            if (!entity) {
                throw new Error("Entity State Unavailable");
            }

            if (showProjectName) {
                // TODO: link to todoist
                content += `<div class="project">${entity.attributes.friendly_name}</div>`;
            }

            let tasks = [];
            entity.attributes.tasks.slice(0, maxEntries).forEach(task => {
                let dueTo = '';
                if (task.due && task.due.date) {
                    // Parse due date
                    let parsedDate = new Date(task.due.date);
                    dueTo += MONTHS[parsedDate.getMonth()] + ' ' + parsedDate.getDate();
                }
                if (task.due && task.due.datetime != null) {
                    // Parse due time
                    let parsedDate = new Date(task.due.datetime);
                    dueTo += ' ' + parsedDate.getHours() + ':' + parsedDate.getMinutes().toString().padStart(2, '0');
                }

                let taskElement = `<li class="task" id="${task.id}"><div><div>${task.content}</div>`;
                if (dueTo) {
                    taskElement += `<div class="due-date">${dueTo}</div>`;
                }
                taskElement += `</div></li>`;

                tasks.push(taskElement);
            });

            content += `<ul class="tasks" id="todoist-tasks-${entityId}">` + tasks.join("\n") + `</ul>`;
        }

        this.shadowRoot.getElementById('container').innerHTML = content;

        let projectElements = this.shadowRoot.querySelectorAll('[id^="todoist-tasks-"]');
        projectElements.forEach(projectElement => {
            projectElement.childNodes.forEach(taskElement => {
                if (hass.states[INPUT_TEXT_ENTITY_ID].state === taskElement.id) {
                    taskElement.classList.add('checked');
                }

                taskElement.addEventListener('click',
                    function (ev) {
                        const parent = ev.target.closest('.task');
                        if (parent && !parent.classList.contains('checked')) {
                            // Disallow unselecting a task ^
                            hass.callService("input_text", "set_value", {
                                entity_id: INPUT_TEXT_ENTITY_ID,
                                value: parent.id
                            }).then(
                                function (response) {},
                                function (error) {
                                    console.log(`Failed to push new task ID to ${INPUT_TEXT_ENTITY_ID}`)
                                });
                        }
                    }, false);
            });
        })
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
        return 5; // TODO: adapt to # entities
    }
}

customElements.define('todoist-card', TodoistCard);