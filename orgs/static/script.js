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
    
    const descriptionBlocks = document.querySelectorAll('.me-description-block');

    descriptionBlocks.forEach(block => {
    block.addEventListener('click', () => {
        block.classList.toggle('expanded');
    });
    console.log()
});
        const activityForm = document.getElementById("activity-form");
    const defaultLocationId = activityForm ? activityForm.dataset.defaultLocation : "";
    
    function wireSessionRow(row) {
        const formatField = row.querySelector("select[name$='session_format']");
        const locationField = row.querySelector("select[name$='location']");
        
        if (!formatField || !locationField) return;
        formatField.addEventListener("change", function(){
            const format = formatField.value;
            const currentLocation = locationField.value;
            if ((format === "i" || format ==="b") && !currentLocation && defaultLocationId) {
                locationField.value = defaultLocationId;
            }
        });
    }
    document.querySelectorAll(".formset-row").forEach(row => {
        if (!row.classList.contains("form-template")){
            wireSessionRow(row);
        }
    });
    document.addEventListener("click", function(e) {
    if (e.target && e.target.id === "add-btn") {
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
        newRow.style.display = "table-row";
        newRow.classList.remove("form-template");
        newRow.innerHTML = newRow.innerHTML.replace(/__prefix__/g, formIndex);

        tbody.appendChild(newRow);
        totalForms.value = formIndex + 1;
        wireSessionRow(newRow);
    }
});

    console.log("finished with add button")
});