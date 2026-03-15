// --- global URL for AJAX ---
console.log("FORMSET SCRIPT LOADED");

// --- run after DOM is ready ---
document.addEventListener("DOMContentLoaded", function () {
    console.log("DOM fully loaded and parsed");
    const tabButtons = document.querySelectorAll('#eventTabs button[data-bs-toggle="tab"]');

    tabButtons.forEach(btn => {
        btn.addEventListener('shown.bs.tab', function (event) {
        // event.target = newly activated tab button
        const targetId = event.target.getAttribute('data-bs-target'); // e.g. "#online"
        history.replaceState(null, '', targetId); // updates URL hash without reloading
        });
    });


    // Check if the URL has a hash like #activity-123
    const hash = window.location.hash;

    if (hash) {
        const targetEl = document.querySelector(hash);
            if (targetEl) {

                targetEl.scrollIntoView({ behavior: "smooth", block: "start" });

                const tabPane =targetEl.classList.contains("tab-pane")
                        ? targetEl
                        : targetEl.closest(".tab-pane");
                if (tabPane && !tabPane.classList.contains("show", "active")) {
                    const tabId = tabPane.id;
                    const tabButton = document.querySelector(`[data-bs-target="#${tabId}"]`);
                    if (tabButton) {
                        const tab = new bootstrap.Tab(tabButton);
                        tab.show();
                    }
                }

            }
        }
    console.log("finished with hash code")
    
    const addBtn = document.getElementById("add-btn");
    console.log("Add button:", addBtn);
    if (addBtn) {
        addBtn.addEventListener("click", function () {
            const container = document.querySelector(".formset");
            const totalForms = document.querySelector("[id$='-TOTAL_FORMS']");
            const template = document.querySelector(".form-template");
            const tbody = document.querySelector(".formset-table tbody");
            console.log("Add button clicked", { container, totalForms, template, tbody });

            if (!container || !totalForms || !template || !tbody) return;

            const emptyHint = document.querySelector(".empty-hint");
            if (emptyHint) emptyHint.remove();

            const formIndex = parseInt(totalForms.value);
            const newRow = template.cloneNode(true);
            newRow.style.display = "";
            newRow.classList.remove("form-template");
            newRow.innerHTML = newRow.innerHTML.replace(/__prefix__/g, formIndex);

            tbody.appendChild(newRow);
            totalForms.value = formIndex + 1;
        });
    }
    console.log("finished with add button")
    document.addEventListener("click", function (e) {

        const block = e.target.closest(".description-block");
        if (!block) return;
        console.log("have block")
        const shortText = block.querySelector(".desc-short");
        const fullText = block.querySelector(".desc-full");
        const toggle = block.querySelector(".toggle-desc");

        shortText.classList.toggle("d-none");
        fullText.classList.toggle("d-none");

        if (toggle) {
            toggle.textContent =
                shortText.classList.contains("d-none") ? "▲" : "▼";
        }

    });
});
