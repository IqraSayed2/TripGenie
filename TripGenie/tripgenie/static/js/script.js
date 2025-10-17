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
