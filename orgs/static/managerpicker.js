document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".manager-picker-form").forEach(function (form) {
    const searchInput = form.querySelector(".manager-search-input");
    const resultsBox = form.querySelector(".manager-results");
    const hiddenProfileId = form.querySelector(".manager-profile-id");
    const selectedBox = form.querySelector(".manager-selected");
    const selectedLabel = form.querySelector(".manager-selected-label");

    if (!searchInput || !resultsBox || !hiddenProfileId || !selectedBox || !selectedLabel) {
      console.log("manager picker wiring failed", {
        searchInput,
        resultsBox,
        hiddenProfileId,
        selectedBox,
        selectedLabel
      });
      return;
    }

    let timer = null;

    searchInput.addEventListener("input", function () {
      const q = searchInput.value.trim();

      hiddenProfileId.value = "";
      selectedBox.classList.add("d-none");
      selectedLabel.textContent = "";
      resultsBox.innerHTML = "";

      const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailPattern.test(q)) return;

      clearTimeout(timer);
      timer = setTimeout(function () {
        fetch(`/orgs/manager-search/?q=${encodeURIComponent(q)}`)
          .then(function (response) {
            return response.json();
          })
          .then(function (data) {
            console.log("manager search data", data);
            resultsBox.innerHTML = "";

            if (!data.results || data.results.length === 0) {
              resultsBox.innerHTML = '<div class="list-group-item text-muted">No matching users found</div>';
              return;
            }

            data.results.forEach(function (item) {
              const btn = document.createElement("button");
              btn.type = "button";
              btn.className = "list-group-item list-group-item-action";
              btn.innerHTML = `
                <div><strong>${item.email || ""}</strong></div>
                <div class="small text-muted">${item.display_name || ""}</div>
                <div class="small text-muted">${item.username || ""}</div>
              `;

              btn.addEventListener("click", function () {
                console.log("selected manager", item);
                hiddenProfileId.value = item.profile_id;
                searchInput.value = item.email || "";
                selectedLabel.textContent = item.display_name
                  ? `${item.display_name} (${item.email})`
                  : (item.email || item.username || "Selected user");
                selectedBox.classList.remove("d-none");
                resultsBox.innerHTML = "";
              });

              resultsBox.appendChild(btn);
            });
          })
          .catch(function (error) {
            console.error("manager search failed", error);
            resultsBox.innerHTML = '<div class="list-group-item text-danger">Search failed</div>';
          });
      }, 250);
    });

    form.addEventListener("submit", function (e) {
      console.log("submitting manager form with profile_id =", hiddenProfileId.value);
      if (!hiddenProfileId.value) {
        e.preventDefault();
        alert("Please choose a user from the search results.");
      }
    });
  });
});