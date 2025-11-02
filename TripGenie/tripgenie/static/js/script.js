//================================ SIGNUP PAGE ========================================

function checkPasswordStrength(input) {
  const password = input.value;
  const minLength = 8;
  const hasUpperCase = /[A-Z]/.test(password);
  const hasLowerCase = /[a-z]/.test(password);
  const hasNumbers = /\d/.test(password);

  if (
    password.length < minLength ||
    !hasUpperCase ||
    !hasLowerCase ||
    !hasNumbers
  ) {
    input.setCustomValidity(
      "Password must be at least 8 characters with uppercase, lowercase and numbers"
    );
  } else {
    input.setCustomValidity("");
  }
}

function checkPasswordMatch() {
  const password = document.querySelector('input[name="password"]').value;
  const confirmPassword = document.querySelector(
    'input[name="confirmpassword"]'
  ).value;
  const matchDisplay = document.getElementById("passwordMatch");

  if (password === confirmPassword && password !== "") {
    matchDisplay.textContent = "Passwords match";
    matchDisplay.classList.add("match");
    matchDisplay.classList.remove("no-match");
  } else {
    matchDisplay.textContent = "Passwords do not match";
    matchDisplay.classList.add("no-match");
    matchDisplay.classList.remove("match");
  }
}

// Add some interactive feedback
document.querySelectorAll(".signup-form-input").forEach((input) => {
  input.addEventListener("focus", function () {
    this.parentElement.style.transform = "scale(1.01)";
    this.parentElement.style.transition = "transform 0.2s ease";
  });

  input.addEventListener("blur", function () {
    this.parentElement.style.transform = "scale(1)";
  });
});

//================================ LOGIN PAGE ========================================

// Add some interactive feedback
document.querySelectorAll(".form-input").forEach((input) => {
  input.addEventListener("focus", function () {
    this.parentElement.style.transform = "scale(1.02)";
    this.parentElement.style.transition = "transform 0.2s ease";
  });

  input.addEventListener("blur", function () {
    this.parentElement.style.transform = "scale(1)";
  });
});

//=================================== FAQS =============================================

document.addEventListener("DOMContentLoaded", function () {
  const categoryButtons = document.querySelectorAll(".faq-category-btn");
  const faqContentSections = document.querySelectorAll(".faq-category-content");

  // Function to show/hide content based on category
  function showCategory(category) {
    faqContentSections.forEach((section) => {
      if (section.getAttribute("data-category") === category) {
        section.classList.remove("d-none");
      } else {
        section.classList.add("d-none");
      }
    });
  }

  // Add event listeners to buttons
  categoryButtons.forEach((button) => {
    button.addEventListener("click", function () {
      // Remove active class from all buttons
      categoryButtons.forEach((btn) => btn.classList.remove("active"));
      // Add active class to the clicked button
      this.classList.add("active");
      // Show the corresponding FAQ content
      const category = this.getAttribute("data-filter");
      showCategory(category);
    });
  });

  // Handle search bar functionality (optional, basic filtering)
  const searchBar = document.querySelector(".faq-search-bar");
  searchBar.addEventListener("input", function () {
    const query = this.value.toLowerCase();
    const allAccordionItems = document.querySelectorAll(".accordion-item");

    allAccordionItems.forEach((item) => {
      const headerText = item
        .querySelector(".accordion-header")
        .textContent.toLowerCase();
      const bodyText = item.querySelector(".accordion-body")
        ? item.querySelector(".accordion-body").textContent.toLowerCase()
        : "";

      if (headerText.includes(query) || bodyText.includes(query)) {
        item.style.display = "block"; // Show item
      } else {
        item.style.display = "none"; // Hide item
      }
    });
  });
});
