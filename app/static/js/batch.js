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