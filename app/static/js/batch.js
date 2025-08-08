try {
    const response = await fetch("/upload", {
        method: "POST",
        headers: {
            "Content-Type": "application/json", // Required for Flask to parse JSON
        },
        body: JSON.stringify({ csvData: rows }), // Send parsed CSV data
    });

    if (!response.ok) {
        throw new Error(`Server returned status ${response.status}`);
    }

    const result = await response.json();

    // Log entire result to console
    console.log("Full Response:", result);

    // Log each result row nicely
    if (Array.isArray(result.results)) {
        result.results.forEach((row, index) => {
            console.log(`--- Row ${index + 1} ---`);
            console.table(row); // Nicely formatted table in console
        });
    } else {
        console.warn("Unexpected response format:", result);
    }

} catch (error) {
    console.error("Error uploading CSV data:", error);
}


document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("save-batch").addEventListener("click", function () {
        alert("Save button clicked!");
    });
});



// document.getElementById("save-batch").addEventListener("click", function () {
//     alert(0);
//     fetch("/get_latest_batch_predictions")
//         .then((response) => response.json())
//         .then((data) => {
//             if (data.error) {
//                 alert(data.error);
//                 return;
//             }

//             // Send to backend to save
//             fetch("/save-prediction-batch", {
//                 method: "POST",
//                 headers: {
//                     "Content-Type": "application/json",
//                 },
//                 body: JSON.stringify(data),
//             })
//                 .then((response) => response.json())
//                 .then((result) => {
//                     window.location.href = result.redirect;
//                 })
//                 .catch((err) => {
//                     console.error("Save failed:", err);
//                     alert("Save failed.");
//                 });
//         })
//         .catch((err) => {
//             console.error("Fetch failed:", err);
//             alert("Could not fetch prediction data.");
//         });
// });