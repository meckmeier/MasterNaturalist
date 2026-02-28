// --- global URL for AJAX ---
const loadOrgLocUrl = "/ajax/load-orgloc/";

function sortOrgLocDropdown() {
    const orgSelect = document.getElementById("id_org");
    const locSelect = document.getElementById("id_orgloc");
    if (!orgSelect || !locSelect) return;

    const selectedOrgId = orgSelect.value;
    const options = Array.from(locSelect.options);

    // Separate options into "matches selected org" and others
    const matches = [];
    const others = [];

    options.forEach(opt => {
        if (!opt.value) return; // skip blank option
        const locOrgId = opt.dataset.orgId; // assumes each option has data-org-id
        if (locOrgId === selectedOrgId) {
            matches.push(opt);
        } else {
            others.push(opt);
        }
    });

    // Sort each list alphabetically by option text
    matches.sort((a, b) => a.text.localeCompare(b.text));
    others.sort((a, b) => a.text.localeCompare(b.text));

    // Rebuild the dropdown
    locSelect.innerHTML = "";
    const emptyOption = document.createElement("option");
    emptyOption.value = "";
    emptyOption.textContent = "---------";
    locSelect.appendChild(emptyOption);

    [...matches, ...others].forEach(opt => locSelect.appendChild(opt));

    // Keep the previously selected value
    if (locSelect.dataset.current) {
        locSelect.value = locSelect.dataset.current;
    }
}


// --- run after DOM is ready ---
document.addEventListener("DOMContentLoaded", function () {
     const orgSelect = document.getElementById("id_org");
    if (!orgSelect) return;

    orgSelect.addEventListener("change", sortOrgLocDropdown);

    // Initial sort
    sortOrgLocDropdown();

    
    // --- rest of your formset add row logic stays unchanged ---
    const addBtn = document.getElementById("add-btn");
    if (addBtn) {
        addBtn.addEventListener("click", function () {
            const container = document.querySelector(".formset");
            const totalForms = document.querySelector("#id_locations-TOTAL_FORMS");
            const template = document.querySelector(".form-template");
            const tbody = document.querySelector(".formset-table tbody");

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
});