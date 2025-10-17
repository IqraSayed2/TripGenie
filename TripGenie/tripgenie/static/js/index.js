document.addEventListener("DOMContentLoaded", function () {
  const themeToggle = document.getElementById("themeToggle");
  const body = document.body;

  // Load saved theme
  if (localStorage.getItem("theme") === "light") {
    body.classList.remove("dark-theme");
    body.classList.add("light-theme");
    themeToggle.checked = false;
  } else {
    body.classList.add("dark-theme");
    body.classList.remove("light-theme");
    themeToggle.checked = true;
  }

  themeToggle.addEventListener("change", () => {
    if (themeToggle.checked) {
      body.classList.add("dark-theme");
      body.classList.remove("light-theme");
      localStorage.setItem("theme", "dark");
    } else {
      body.classList.remove("dark-theme");
      body.classList.add("light-theme");
      localStorage.setItem("theme", "light");
    }
  });
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

function setTheme(theme) {
  if (theme === "dark") {
    body.classList.remove("light-theme");
    body.classList.add("dark-theme");
    icon.classList.remove("fa-sun");
    icon.classList.add("fa-moon");
    themeToggle.title = "Switch to light theme";
  } else {
    body.classList.remove("dark-theme");
    body.classList.add("light-theme");
    icon.classList.remove("fa-moon");
    icon.classList.add("fa-sun");
    themeToggle.title = "Switch to dark theme";
  }
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
    navbar.style.background = body.classList.contains("dark-theme")
      ? "rgba(15, 23, 42, 0.95)"
      : "rgba(255, 255, 255, 0.95)";
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

// Parallax effect for bubbles
window.addEventListener("mousemove", function (e) {
  if (body.classList.contains("dark-theme")) {
    const bubbles = document.querySelectorAll(".bubble");
    const x = e.clientX / window.innerWidth;
    const y = e.clientY / window.innerHeight;

    bubbles.forEach((bubble, index) => {
      const speed = (index + 1) * 0.5;
      const xOffset = (x - 0.5) * speed * 50;
      const yOffset = (y - 0.5) * speed * 50;
      bubble.style.transform += ` translate(${xOffset}px, ${yOffset}px)`;
    });
  }
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
