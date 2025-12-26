document.addEventListener("DOMContentLoaded", function () {
  const body = document.body;

  // Always set light theme
  body.classList.add("light-theme");
  localStorage.setItem("theme", "light");
});

// Language and Currency Selection
let selectedLang = "eng";
let selectedCurrency = "INR";

document.querySelectorAll(".lang-item").forEach((item) => {
  item.addEventListener("click", function () {
    document
      .querySelectorAll(".lang-item")
      .forEach((i) => i.classList.remove("selected"));
    this.classList.add("selected");
    selectedLang = this.dataset.lang;
    updateSelector();
  });
});

document.querySelectorAll(".currency-item").forEach((item) => {
  item.addEventListener("click", function () {
    document
      .querySelectorAll(".currency-item")
      .forEach((i) => i.classList.remove("selected"));
    this.classList.add("selected");
    selectedCurrency = this.dataset.currency;
    updateSelector();
  });
});

function updateSelector() {
  const langText =
    selectedLang === "eng"
      ? "Eng"
      : selectedLang === "es"
      ? "Esp"
      : selectedLang === "fr"
      ? "Fra"
      : selectedLang === "de"
      ? "Deu"
      : selectedLang === "zh"
      ? "中文"
      : selectedLang === "jp"
      ? "日本"
      : selectedLang === "kr"
      ? "한국"
      : selectedLang === "ar"
      ? "عربي"
      : selectedLang.toUpperCase().substring(0, 3);

  document.querySelector(
    ".combined-selector"
  ).textContent = `${langText} | ${selectedCurrency}`;
}

// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute("href"));
    if (target) {
      target.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  });
});

// Navbar background on scroll
window.addEventListener("scroll", function () {
  const navbar = document.querySelector(".navbar");
  if (window.scrollY > 100) {
    navbar.style.background = "rgba(255, 255, 255, 0.95)";
  } else {
    navbar.style.background = "transparent";
  }
});

// Add floating animation to buttons
document.querySelectorAll(".btn").forEach((btn) => {
  btn.addEventListener("mouseenter", function () {
    this.style.transform = "translateY(-3px)";
  });

  btn.addEventListener("mouseleave", function () {
    this.style.transform = "translateY(0)";
  });
});

//reviews ===============================================

// Add interactive star hover effect
document.querySelectorAll(".tripgenie-review-card").forEach((card) => {
  const stars = card.querySelectorAll(".tripgenie-star-icon");

  card.addEventListener("mouseenter", () => {
    stars.forEach((star, index) => {
      setTimeout(() => {
        star.style.transform = "scale(1.2)";
        star.style.transition = "transform 0.2s ease";
      }, index * 50);
    });
  });

  card.addEventListener("mouseleave", () => {
    stars.forEach((star) => {
      star.style.transform = "scale(1)";
    });
  });
});

// Intersection Observer for animation trigger
const observerOptions = {
  threshold: 0.1,
  rootMargin: "0px 0px -50px 0px",
};

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.style.animationPlayState = "running";
    }
  });
}, observerOptions);

document.querySelectorAll(".tripgenie-review-card").forEach((card) => {
  card.style.animationPlayState = "paused";
  observer.observe(card);
});
