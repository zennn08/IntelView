// Drag and drop functionality
const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("video");

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.style.borderColor = "rgba(102, 126, 234, 1)";
  dropZone.style.background = "rgba(255, 255, 255, 0.08)";
});

dropZone.addEventListener("dragleave", () => {
  dropZone.style.borderColor = "rgba(102, 126, 234, 0.5)";
  dropZone.style.background = "rgba(255, 255, 255, 0.03)";
});

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.style.borderColor = "rgba(102, 126, 234, 0.5)";
  dropZone.style.background = "rgba(255, 255, 255, 0.03)";

  const files = e.dataTransfer.files;
  if (files.length > 0) {
    fileInput.files = files;
    dropZone.querySelector("p").textContent = files[0].name;
  }
});

fileInput.addEventListener("change", () => {
  if (fileInput.files.length > 0) {
    dropZone.querySelector("p").textContent = fileInput.files[0].name;
  }
});

// Analyze button functionality
document.getElementById("analyzeBtn").addEventListener("click", async () => {
  const file = document.getElementById("video").files[0];
  if (!file) {
    alert("Please upload a video first!");
    return;
  }

  const resultSection = document.getElementById("result-section");
  resultSection.classList.add("hidden");

  const form = new FormData();
  form.append("video", file);

  const btn = document.getElementById("analyzeBtn");
  btn.textContent = "Processing...";
  btn.disabled = true;
  btn.classList.add("loading");

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      body: form,
    });

    const data = await response.json();

    document.getElementById("speechText").textContent = data.transcript;
    document.getElementById("acousticConfscore").textContent = data.speech.acoustic_confidence;

    document.getElementById("peopleDetect").textContent = data.people.cheating_detected ? "True" : "False";
    document.getElementById("event").textContent = data.people.total_events;
    document.getElementById("peopleConf").textContent = data.people.confidence_score;

    document.getElementById("eyeDetect").textContent = data.eye.cheating_detected ? "True" : "False";
    document.getElementById("eyeEvent").textContent = data.eye.total_events;
    document.getElementById("eyeConf").textContent = data.eye.confidence_score;

    document.getElementById("score").textContent = data.evaluation.score;
    document.getElementById("scoreConf").textContent = data.confidence_score;
    document.getElementById("reason").textContent = data.evaluation.reason;
    document.getElementById("cheatingEval").textContent = data.evaluation.cheating_indication;
    document.getElementById("cheatingReason").textContent = data.evaluation.cheating_reason;
    document.getElementById("feedback").textContent = data.evaluation.feedback;
    document.getElementById("timeExecution").textContent = data.execution_time_seconds + " sec";

    resultSection.classList.remove("hidden");

    document.querySelectorAll(".card").forEach((card, i) => {
      setTimeout(() => {
        card.classList.add("show");
      }, 200 * i);
    });

    // Smooth scroll to results
    setTimeout(() => {
      resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 400);
  } catch (error) {
    alert("Error: " + error);
  }

  btn.textContent = "Analyze Video";
  btn.disabled = false;
  btn.classList.remove("loading");
});

// Export PDF functionality
document.getElementById("exportPdfBtn").addEventListener("click", () => {
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF();

  const score = document.getElementById("score").textContent;
  const reason = document.getElementById("reason").textContent;
  const cheating = document.getElementById("cheatingEval").textContent;
  const feedback = document.getElementById("feedback").textContent;
  const timeExecution = document.getElementById("timeExecution").textContent;

  // Set colors
  const primaryColor = [50, 50, 50];
  const textColor = [50, 50, 50];

  // Title
  doc.setFontSize(24);
  doc.setTextColor(...primaryColor);
  doc.text("INTELVIEW", 105, 20, { align: "center" });

  doc.setFontSize(16);
  doc.text("Evaluation Report", 105, 30, { align: "center" });

  // Line separator
  doc.setDrawColor(...primaryColor);
  doc.setLineWidth(0.5);
  doc.line(20, 35, 190, 35);

  // Date
  doc.setFontSize(10);
  doc.setTextColor(...textColor);
  doc.text(`Generated: ${new Date().toLocaleString()}`, 20, 45);

  // Content
  let yPos = 60;
  doc.setFontSize(12);
  doc.setTextColor(...primaryColor);

  // Score
  doc.text("Score:", 20, yPos);
  doc.setTextColor(...textColor);
  doc.text(score, 50, yPos);
  yPos += 15;

  // Reason
  doc.setTextColor(...primaryColor);
  doc.text("Reason:", 20, yPos);
  yPos += 7;
  doc.setTextColor(...textColor);
  doc.setFontSize(10);
  const reasonLines = doc.splitTextToSize(reason, 170);
  doc.text(reasonLines, 20, yPos);
  yPos += reasonLines.length * 5 + 10;

  // Cheating
  doc.setFontSize(12);
  doc.setTextColor(...primaryColor);
  doc.text("Cheating Indication:", 20, yPos);
  yPos += 7;
  doc.setTextColor(...textColor);
  doc.setFontSize(10);
  const cheatingLines = doc.splitTextToSize(cheating, 170);
  doc.text(cheatingLines, 20, yPos);
  yPos += cheatingLines.length * 5 + 10;

  // Feedback
  doc.setFontSize(12);
  doc.setTextColor(...primaryColor);
  doc.text("Feedback:", 20, yPos);
  yPos += 7;
  doc.setTextColor(...textColor);
  doc.setFontSize(10);
  const feedbackLines = doc.splitTextToSize(feedback, 170);
  doc.text(feedbackLines, 20, yPos);
  yPos += feedbackLines.length * 5 + 10;

  // Time Execution
  doc.setFontSize(12);
  doc.setTextColor(...primaryColor);
  doc.text("Time Execution:", 20, yPos);
  doc.setTextColor(...textColor);
  doc.text(timeExecution, 65, yPos);

  // Footer
  doc.setFontSize(8);
  doc.setTextColor(150, 150, 150);
  doc.text("Report generated by INTELVIEW AI Interview Analyzer", 105, 280, {
    align: "center",
  });

  // Save PDF
  doc.save(`INTELVIEW_Report_${new Date().getTime()}.pdf`);
});

// Navbar scroll effect
const navbar = document.getElementById('navbar');
const navToggle = document.getElementById('navToggle');
const navMenu = document.getElementById('navMenu');

window.addEventListener('scroll', () => {
  if (window.scrollY > 50) {
    navbar.classList.add('scrolled');
  } else {
    navbar.classList.remove('scrolled');
  }
});

// Mobile menu toggle
navToggle.addEventListener('click', () => {
  navToggle.classList.toggle('active');
  navMenu.classList.toggle('active');
});

// Close menu when clicking on a link
const navLinks = document.querySelectorAll('.navbar-menu a');
navLinks.forEach(link => {
  link.addEventListener('click', () => {
    navToggle.classList.remove('active');
    navMenu.classList.remove('active');
  });
});

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    }
  });
});
