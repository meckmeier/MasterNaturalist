// --- global URL for AJAX ---
const loadOrgLocUrl = "/ajax/load-orgloc/";  // hardcoded or from template


// --- helper function to populate OrgLoc dropdown ---
function populateOrgLoc(locSelect, data) {
    locSelect.disabled = false;
    locSelect.innerHTML = '<option value="">---------</option>'; 

    const currentValue = locSelect.value || locSelect.dataset.current; //saved value
    
    data.forEach(loc => {
        const option = document.createElement("option");
        option.value = loc.id;
        option.textContent = loc.loc_name;

        if (currentValue && loc.id == currentValue) {
                option.selected = true;
            }

        locSelect.appendChild(option);
    });
}

// --- fetch OrgLocs from server ---
function loadOrgLocs() {
    
    const orgSelect = document.getElementById("id_org");
    const locSelect = document.getElementById("id_orgloc");
    console.log("loading orglocs for org id:", orgSelect.value)
    if (!orgSelect || !locSelect) return;

    const orgId = orgSelect.value;
    console.log("selected orgid:", orgId)

    if (!orgId) {
        locSelect.disabled = true;
        return;
    }

    fetch(`${loadOrgLocUrl}?org_id=${orgId}`)
        .then(response => response.json())
        .then(data => {console.log ("ajax returned",data);
            populateOrgLoc(locSelect, data);})
        .catch(err => console.error("Failed to load OrgLoc:", err));
}

// --- run after DOM is ready ---
document.addEventListener("DOMContentLoaded", function () {
    const orgSelect = document.getElementById("id_org");


    if (orgSelect) {
        // bind change event
        orgSelect.addEventListener("change", loadOrgLocs);

        // initial load if org already has a value
        if (orgSelect.value) {
            loadOrgLocs();
        }
    }
    /* ========= FORMSET ADD ROW ========= */

    const addBtn = document.getElementById("add-btn");
    console.log("addBtn")
    console.log(addBtn)
    if (addBtn) {

    addBtn.addEventListener("click", function () {

        const container = document.querySelector(".formset");
        const totalForms = document.querySelector("#id_locations-TOTAL_FORMS");
        const template = document.querySelector(".form-template");
        const tbody = document.querySelector(".formset-table tbody");

        if (!container || !totalForms || !template || !tbody) {
            console.log("Formset pieces missing");
            return;
        }

        // 🔴 remove empty hint row if present
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