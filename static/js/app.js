document.getElementById("analyzeBtn").addEventListener("click", async () => {
    const fileInput = document.getElementById("video");
    const resultBox = document.getElementById("result");

    if (!fileInput.files.length) {
        resultBox.textContent = "Please upload a video first.";
        return;
    }

    let form = new FormData();
    form.append("video", fileInput.files[0]);

    resultBox.textContent = "Processing video...\nThis may take 1–3 minutes.";

    try {
        let response = await fetch("http://localhost:5000/analyze", {
            method: "POST",
            body: form
        });

        let data = await response.json();
        resultBox.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
        resultBox.textContent = "Error: " + error;
    }
});
