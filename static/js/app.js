// Global variable to store analyze response data
let analyzeResponseData = null;
let videoEntryCount = 0;

// Function to update all video numbers
function updateVideoNumbers() {
  const entries = document.querySelectorAll(".video-entry");
  entries.forEach((entry, index) => {
    const header = entry.querySelector("h3");
    if (header) {
      header.textContent = `Video ${index + 1}`;
    }
  });
}

// Function to create a video entry
function createVideoEntry() {
  videoEntryCount++;
  const entryId = `video-entry-${videoEntryCount}`;

  const entryDiv = document.createElement("div");
  entryDiv.id = entryId;
  entryDiv.className = "video-entry";
  entryDiv.style.cssText = `
    margin-bottom: 20px;
    padding: 25px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(102, 126, 234, 0.3);
    border-radius: 10px;
    position: relative;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
  `;

  // Get current count for initial display
  const currentCount = document.querySelectorAll(".video-entry").length + 1;

  entryDiv.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px;">
      <h3 style="color: #667eea; margin: 0; font-size: 20px;">Video ${currentCount}</h3>
      <button class="remove-video-btn" data-entry-id="${entryId}" style="background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid #ef4444; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: bold;">
        🗑️ Remove
      </button>
    </div>

    <div style="margin-bottom: 20px;">
      <label style="display: block; color: #fff; margin-bottom: 10px; font-weight: bold; font-size: 15px;">Video File:</label>
      <div class="upload-zone-small" style="padding: 25px 20px; border: 2px dashed rgba(102, 126, 234, 0.5); border-radius: 8px; text-align: center; cursor: pointer; transition: all 0.3s; background: rgba(255, 255, 255, 0.02);">
        <div class="upload-icon" style="font-size: 40px;">📁</div>
        <p style="margin: 10px 0; color: #888; font-size: 14px;">Click to select video</p>
        <input type="file" class="video-file-input" accept="video/*" style="display: none;">
        <span class="file-name" style="color: #667eea; font-size: 13px; word-break: break-all;"></span>
      </div>
    </div>

    <div>
      <label style="display: block; color: #fff; margin-bottom: 10px; font-weight: bold; font-size: 15px;">Interview Question:</label>
      <textarea
        class="question-input"
        placeholder="Enter the interview question (e.g., Can you share any specific challenges you faced while working on certification and how you overcame them?)"
        style="width: 100%; min-height: 100px; padding: 15px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(102, 126, 234, 0.5); border-radius: 8px; color: #fff; font-size: 14px; resize: vertical; font-family: inherit; box-sizing: border-box;"
      ></textarea>
      <div style="margin-top: 8px; color: #888; font-size: 12px;">
        💡 Leave blank to use default rubric
      </div>
    </div>
  `;

  // Add click handler for upload zone
  const uploadZone = entryDiv.querySelector(".upload-zone-small");
  const fileInput = entryDiv.querySelector(".video-file-input");
  const fileNameSpan = entryDiv.querySelector(".file-name");

  uploadZone.addEventListener("click", () => {
    fileInput.click();
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      const fileName = e.target.files[0].name;
      fileNameSpan.textContent = `Selected: ${fileName}`;
      uploadZone.style.borderColor = "rgba(102, 126, 234, 1)";
    }
  });

  return entryDiv;
}

// Function to add video entry
function addVideoEntry() {
  const container = document.getElementById("videoEntriesContainer");
  const entry = createVideoEntry();
  container.appendChild(entry);

  // Add remove button event listener
  const removeBtn = entry.querySelector(".remove-video-btn");
  removeBtn.addEventListener("click", () => {
    removeVideoEntry(removeBtn.dataset.entryId);
  });

  // Add animation
  setTimeout(() => {
    entry.style.opacity = "0";
    entry.style.transform = "translateY(-10px)";
    entry.style.transition = "all 0.3s";
    setTimeout(() => {
      entry.style.opacity = "1";
      entry.style.transform = "translateY(0)";
    }, 10);
  }, 0);
}

// Function to remove video entry
function removeVideoEntry(entryId) {
  const entries = document.querySelectorAll(".video-entry");

  // Don't allow removing if only one entry left
  if (entries.length <= 1) {
    alert("At least one video entry is required!");
    return;
  }

  const entry = document.getElementById(entryId);
  if (entry) {
    entry.style.transition = "all 0.3s";
    entry.style.opacity = "0";
    entry.style.transform = "translateX(20px)";
    setTimeout(() => {
      entry.remove();
      // Update all video numbers after removal
      updateVideoNumbers();
    }, 300);
  }
}

// Add video button handler
document.getElementById("addVideoBtn").addEventListener("click", () => {
  addVideoEntry();
});

// Initialize with one video entry
addVideoEntry();

// Analyze button functionality
document.getElementById("analyzeBtn").addEventListener("click", async () => {
  // Collect all video entries
  const videoEntries = document.querySelectorAll(".video-entry");

  if (videoEntries.length === 0) {
    alert("Please add at least one video!");
    return;
  }

  // Validate that all entries have files
  const videosData = [];
  for (let i = 0; i < videoEntries.length; i++) {
    const entry = videoEntries[i];
    const fileInput = entry.querySelector(".video-file-input");
    const questionInput = entry.querySelector(".question-input");

    if (!fileInput.files || fileInput.files.length === 0) {
      alert(`Please select a video file for Video ${i + 1}`);
      return;
    }

    videosData.push({
      file: fileInput.files[0],
      question: questionInput.value.trim()
    });
  }

  const resultSection = document.getElementById("result-section");
  const singleResult = document.getElementById("single-result");
  const multipleResults = document.getElementById("multiple-results");

  resultSection.classList.add("hidden");
  singleResult.classList.add("hidden");
  multipleResults.classList.add("hidden");

  const form = new FormData();

  // Append videos and corresponding questions
  videosData.forEach((data) => {
    form.append("video", data.file);
    form.append("question", data.question);
  });

  const btn = document.getElementById("analyzeBtn");
  const originalText = btn.textContent;
  btn.textContent = videosData.length > 1 ? `Processing ${videosData.length} videos...` : "Processing...";
  btn.disabled = true;
  btn.classList.add("loading");

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      body: form,
    });

    const data = await response.json();

    // Store response data globally for export functionality
    analyzeResponseData = data;

    // Check if multiple videos
    if (data.multiple) {
      renderMultipleResults(data);
    } else {
      renderSingleResult(data);
    }

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

  btn.textContent = originalText;
  btn.disabled = false;
  btn.classList.remove("loading");
});

// Function to render single video result
function renderSingleResult(data) {
  const singleResult = document.getElementById("single-result");

  // Show question if exists
  const questionCard = document.getElementById("questionCard");
  const questionText = document.getElementById("questionText");
  const questionMatchBadge = document.getElementById("questionMatchBadge");

  if (data.question && data.question.trim() !== "") {
    questionText.textContent = data.question;
    questionMatchBadge.innerHTML = getQuestionMatchBadge(data.evaluation.question_match);
    questionCard.style.display = "block";
  } else {
    questionCard.style.display = "none";
  }

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

  singleResult.classList.remove("hidden");
}

// Function to render multiple videos results
function renderMultipleResults(data) {
  const multipleResults = document.getElementById("multiple-results");
  multipleResults.innerHTML = "";

  // Add summary card
  const summaryCard = document.createElement("div");
  summaryCard.className = "card";
  summaryCard.innerHTML = `
    <h3>📊 Analysis Summary</h3>
    <p><b>Total Videos Analyzed:</b> ${data.count}</p>
    <p><b>Overall Confidence Score:</b> ${calculateAverageConfidence(data.results).toFixed(2)}</p>
    <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px;">
      <button id="exportAllPdfBtn" class="export-btn">📄 Export All to PDF</button>
      <button id="exportAllJsonBtn" class="export-btn">📦 Export All to JSON</button>
    </div>
  `;
  multipleResults.appendChild(summaryCard);

  // Add individual results for each video
  data.results.forEach((result, index) => {
    const videoCard = document.createElement("div");
    videoCard.className = "card";
    videoCard.style.marginTop = "20px";

    const questionSection = result.question
      ? `<div style="margin-bottom: 20px; padding: 15px; background: rgba(102, 126, 234, 0.1); border-left: 3px solid rgba(102, 126, 234, 0.8); border-radius: 5px;">
           <h3>❓ Interview Question</h3>
           <p style="font-style: italic;">${result.question}</p>
           ${getQuestionMatchBadge(result.evaluation.question_match)}
         </div>`
      : '';

    videoCard.innerHTML = `
      <h2 style="margin-bottom: 20px;">Video ${index + 1}: ${result.video_name || 'Unknown'}</h2>

      ${questionSection}

      <div style="margin-bottom: 20px;">
        <h3>📝 Speech To Text</h3>
        <p>${result.transcript}</p>
        <p><b>Acoustic Confidence Score:</b> ${result.speech.acoustic_confidence}</p>
      </div>

      <div style="margin-bottom: 20px;">
        <h3>🔍 Cheating Identification</h3>
        <p><b>People Detector:</b> ${result.people.cheating_detected ? "True" : "False"}</p>
        <p><b>Event's People Detector:</b> ${result.people.total_events}</p>
        <p><b>Confidence People Score:</b> ${result.people.confidence_score}</p>
        <p><b>Eye Detector:</b> ${result.eye.cheating_detected ? "True" : "False"}</p>
        <p><b>Event's Eye Detector:</b> ${result.eye.total_events}</p>
        <p><b>Confidence Eye Score:</b> ${result.eye.confidence_score}</p>
      </div>

      <div style="margin-bottom: 20px;">
        <h3>📊 Evaluation Report</h3>
        <p><b>Score:</b> ${result.evaluation.score}</p>
        <p><b>Confidence Score:</b> ${result.confidence_score}</p>
        <p><b>Reason:</b> ${result.evaluation.reason}</p>
        <p><b>Cheating:</b> ${result.evaluation.cheating_indication}</p>
        <p><b>Cheating Reason:</b> ${result.evaluation.cheating_reason}</p>
        <p><b>Feedback:</b> ${result.evaluation.feedback}</p>
        <p><b>Time Execution:</b> ${result.execution_time_seconds} sec</p>
      </div>

      <div style="display: flex; gap: 10px; flex-wrap: wrap;">
        <button class="export-btn export-single-pdf" data-index="${index}">📄 Export to PDF</button>
        <button class="export-btn export-single-json" data-index="${index}">📦 Export to JSON</button>
      </div>
    `;
    multipleResults.appendChild(videoCard);
  });

  multipleResults.classList.remove("hidden");

  // Add event listeners for individual export buttons
  document.querySelectorAll(".export-single-json").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const index = parseInt(e.target.getAttribute("data-index"));
      exportSingleVideoJSON(data.results[index], index);
    });
  });

  document.querySelectorAll(".export-single-pdf").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const index = parseInt(e.target.getAttribute("data-index"));
      exportSingleVideoPDF(data.results[index], index);
    });
  });

  // Add event listener for export all buttons
  document.getElementById("exportAllJsonBtn").addEventListener("click", () => {
    exportMultipleVideosJSON(data);
  });

  document.getElementById("exportAllPdfBtn").addEventListener("click", () => {
    exportAllVideosPDF(data);
  });
}

// Helper function to calculate average confidence
function calculateAverageConfidence(results) {
  const sum = results.reduce((acc, result) => acc + result.confidence_score, 0);
  return sum / results.length;
}

// Helper function to generate question match badge
function getQuestionMatchBadge(questionMatch) {
  if (!questionMatch) {
    return '';
  }

  if (questionMatch.matched) {
    return `
      <div style="margin-top: 10px; padding: 8px; background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 5px; font-size: 12px;">
        <b style="color: #22c55e;">✓ Matched with Standard Question</b><br>
        <span style="color: #888;">Match Score: ${(questionMatch.match_score * 100).toFixed(0)}%</span><br>
        <span style="color: #888; font-style: italic;">${questionMatch.standard_question}</span>
      </div>
    `;
  } else {
    return `
      <div style="margin-top: 10px; padding: 8px; background: rgba(251, 191, 36, 0.1); border: 1px solid rgba(251, 191, 36, 0.3); border-radius: 5px; font-size: 12px;">
        <b style="color: #fbbf24;">⚠ Using Generic Rubric</b><br>
        <span style="color: #888;">No matching standard question found</span>
      </div>
    `;
  }
}

// Function to export single video from multiple results
function exportSingleVideoJSON(result, index) {
  const jsonString = JSON.stringify(result, null, 2);
  const blob = new Blob([jsonString], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `INTELVIEW_Video${index + 1}_${result.video_name || 'Unknown'}_${new Date().getTime()}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// Function to export all videos results
function exportMultipleVideosJSON(data) {
  const jsonString = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonString], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `INTELVIEW_AllVideos_${new Date().getTime()}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// Function to export single video from multiple results to PDF
function exportSingleVideoPDF(result, index) {
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF();

  const videoName = result.video_name || `Video ${index + 1}`;
  const score = result.evaluation.score;
  const confidenceScore = result.confidence_score;
  const reason = result.evaluation.reason;
  const cheating = result.evaluation.cheating_indication;
  const cheatingReason = result.evaluation.cheating_reason;
  const feedback = result.evaluation.feedback;
  const timeExecution = result.execution_time_seconds + " sec";
  const question = result.question || "No question provided";

  // Set colors
  const primaryColor = [50, 50, 50];
  const textColor = [50, 50, 50];
  const accentColor = [102, 126, 234];

  // Title
  doc.setFontSize(24);
  doc.setTextColor(...primaryColor);
  doc.text("INTELVIEW", 105, 20, { align: "center" });

  doc.setFontSize(16);
  doc.text("Evaluation Report", 105, 30, { align: "center" });

  // Video name
  doc.setFontSize(12);
  doc.setTextColor(...accentColor);
  doc.text(videoName, 105, 40, { align: "center" });

  // Line separator
  doc.setDrawColor(...primaryColor);
  doc.setLineWidth(0.5);
  doc.line(20, 45, 190, 45);

  // Date
  doc.setFontSize(10);
  doc.setTextColor(...textColor);
  doc.text(`Generated: ${new Date().toLocaleString()}`, 20, 55);

  // Content
  let yPos = 70;
  doc.setFontSize(12);

  // Question
  if (question && question !== "No question provided") {
    doc.setTextColor(...primaryColor);
    doc.text("Interview Question:", 20, yPos);
    yPos += 7;
    doc.setTextColor(...textColor);
    doc.setFontSize(10);
    const questionLines = doc.splitTextToSize(question, 170);
    doc.text(questionLines, 20, yPos);
    yPos += questionLines.length * 5 + 10;
    doc.setFontSize(12);
  }

  // Score
  doc.setTextColor(...primaryColor);
  doc.text("Score:", 20, yPos);
  doc.setTextColor(...textColor);
  doc.text(`${score}/4`, 50, yPos);
  yPos += 10;

  // Confidence Score
  doc.setTextColor(...primaryColor);
  doc.text("Confidence Score:", 20, yPos);
  doc.setTextColor(...textColor);
  doc.text(String(confidenceScore), 70, yPos);
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
  doc.text("Cheating Detected:", 20, yPos);
  doc.setTextColor(...textColor);
  doc.text(String(cheating), 75, yPos);
  yPos += 10;

  doc.setFontSize(10);
  const cheatingLines = doc.splitTextToSize(cheatingReason, 170);
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
  doc.text(timeExecution, 70, yPos);

  // Footer
  doc.setFontSize(8);
  doc.setTextColor(150, 150, 150);
  doc.text("Report generated by INTELVIEW AI Interview Analyzer", 105, 280, {
    align: "center",
  });

  // Save PDF
  const filename = `INTELVIEW_${videoName.replace(/[^a-z0-9]/gi, '_')}_${new Date().getTime()}.pdf`;
  doc.save(filename);
}

// Function to export all videos to single PDF
function exportAllVideosPDF(data) {
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF();

  const primaryColor = [50, 50, 50];
  const textColor = [50, 50, 50];
  const accentColor = [102, 126, 234];

  let currentPage = 1;

  // Cover page
  doc.setFontSize(28);
  doc.setTextColor(...primaryColor);
  doc.text("INTELVIEW", 105, 80, { align: "center" });

  doc.setFontSize(18);
  doc.text("Multiple Videos Analysis Report", 105, 100, { align: "center" });

  doc.setFontSize(12);
  doc.setTextColor(...textColor);
  doc.text(`Total Videos: ${data.count}`, 105, 120, { align: "center" });
  doc.text(`Average Confidence: ${calculateAverageConfidence(data.results).toFixed(2)}`, 105, 130, { align: "center" });
  doc.text(`Generated: ${new Date().toLocaleString()}`, 105, 140, { align: "center" });

  // Footer on cover
  doc.setFontSize(8);
  doc.setTextColor(150, 150, 150);
  doc.text("Report generated by INTELVIEW AI Interview Analyzer", 105, 280, {
    align: "center",
  });

  // Add each video result
  data.results.forEach((result, index) => {
    doc.addPage();
    currentPage++;

    const videoName = result.video_name || `Video ${index + 1}`;
    const score = result.evaluation.score;
    const confidenceScore = result.confidence_score;
    const reason = result.evaluation.reason;
    const cheating = result.evaluation.cheating_indication;
    const cheatingReason = result.evaluation.cheating_reason;
    const feedback = result.evaluation.feedback;
    const timeExecution = result.execution_time_seconds + " sec";
    const question = result.question || "";

    let yPos = 20;

    // Video header
    doc.setFontSize(18);
    doc.setTextColor(...accentColor);
    doc.text(`Video ${index + 1}: ${videoName}`, 105, yPos, { align: "center" });
    yPos += 10;

    // Line separator
    doc.setDrawColor(...primaryColor);
    doc.setLineWidth(0.5);
    doc.line(20, yPos, 190, yPos);
    yPos += 10;

    doc.setFontSize(10);
    doc.setTextColor(...textColor);

    // Question
    if (question && question.trim() !== "") {
      doc.setFontSize(11);
      doc.setTextColor(...primaryColor);
      doc.text("Interview Question:", 20, yPos);
      yPos += 6;
      doc.setFontSize(9);
      doc.setTextColor(...textColor);
      const questionLines = doc.splitTextToSize(question, 170);
      doc.text(questionLines, 20, yPos);
      yPos += questionLines.length * 4 + 8;
    }

    // Score
    doc.setFontSize(11);
    doc.setTextColor(...primaryColor);
    doc.text("Score:", 20, yPos);
    doc.setTextColor(...textColor);
    doc.text(`${score}/4`, 50, yPos);
    yPos += 8;

    // Confidence
    doc.setTextColor(...primaryColor);
    doc.text("Confidence:", 20, yPos);
    doc.setTextColor(...textColor);
    doc.text(String(confidenceScore), 55, yPos);
    yPos += 12;

    // Reason
    doc.setTextColor(...primaryColor);
    doc.text("Reason:", 20, yPos);
    yPos += 5;
    doc.setTextColor(...textColor);
    doc.setFontSize(9);
    const reasonLines = doc.splitTextToSize(reason, 170);
    doc.text(reasonLines, 20, yPos);
    yPos += reasonLines.length * 4 + 8;

    // Cheating
    doc.setFontSize(11);
    doc.setTextColor(...primaryColor);
    doc.text("Cheating:", 20, yPos);
    doc.setTextColor(...textColor);
    doc.text(String(cheating), 50, yPos);
    yPos += 6;

    doc.setFontSize(9);
    const cheatingLines = doc.splitTextToSize(cheatingReason, 170);
    doc.text(cheatingLines, 20, yPos);
    yPos += cheatingLines.length * 4 + 8;

    // Feedback
    doc.setFontSize(11);
    doc.setTextColor(...primaryColor);
    doc.text("Feedback:", 20, yPos);
    yPos += 5;
    doc.setTextColor(...textColor);
    doc.setFontSize(9);
    const feedbackLines = doc.splitTextToSize(feedback, 170);
    doc.text(feedbackLines, 20, yPos);
    yPos += feedbackLines.length * 4 + 8;

    // Time
    doc.setFontSize(11);
    doc.setTextColor(...primaryColor);
    doc.text("Time:", 20, yPos);
    doc.setTextColor(...textColor);
    doc.text(timeExecution, 40, yPos);

    // Page number
    doc.setFontSize(8);
    doc.setTextColor(150, 150, 150);
    doc.text(`Page ${currentPage}`, 105, 285, { align: "center" });
  });

  // Save PDF
  doc.save(`INTELVIEW_AllVideos_${new Date().getTime()}.pdf`);
}

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

// Export JSON functionality
document.getElementById("exportJsonBtn").addEventListener("click", () => {
  if (!analyzeResponseData) {
    alert("No data available to export. Please analyze a video first.");
    return;
  }

  // Convert data to JSON string with pretty formatting
  const jsonString = JSON.stringify(analyzeResponseData, null, 2);

  // Create a Blob from the JSON string
  const blob = new Blob([jsonString], { type: "application/json" });

  // Create a download link
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `INTELVIEW_Analysis_${new Date().getTime()}.json`;

  // Trigger the download
  document.body.appendChild(link);
  link.click();

  // Clean up
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
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
