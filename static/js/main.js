"use strict";

const predictionForm = document.getElementById("predictionForm");
if (predictionForm) {
  const area = document.getElementById("id_area_sqft");
  const beds = document.getElementById("id_bedrooms");
  const baths = document.getElementById("id_bathrooms");
  const floors = document.getElementById("id_floors");
  const propertyType = document.getElementById("id_property_type");
  const validateDetails = () => {
    area.setCustomValidity("");
    floors.setCustomValidity("");
    if (area.value && beds.value && baths.value && Number(area.value) < 120 * (Number(beds.value) + Number(baths.value))) {
      area.setCustomValidity("Allow at least 120 sq ft per bedroom and bathroom.");
    }
    if (propertyType.value === "Apartment" && floors.value && Number(floors.value) !== 1) {
      floors.setCustomValidity("An apartment's interior occupies one floor in this demo.");
    }
  };
  [area, beds, baths, floors, propertyType].forEach((input) => input.addEventListener("input", validateDetails));
  validateDetails();
  predictionForm.addEventListener("submit", (event) => {
    validateDetails();
    if (!predictionForm.checkValidity()) {
      event.preventDefault();
      predictionForm.reportValidity();
      return;
    }
    const button = document.getElementById("predictButton");
    button.disabled = true;
    button.setAttribute("aria-busy", "true");
    button.querySelector("span").textContent = "Calculating your estimate…";
  });
  window.addEventListener("pageshow", () => {
    const button = document.getElementById("predictButton");
    button.disabled = false;
    button.removeAttribute("aria-busy");
    button.querySelector("span").textContent = "Calculate my estimate";
  });
}
