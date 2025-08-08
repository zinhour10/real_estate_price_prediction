document.addEventListener("DOMContentLoaded", function () {
    document
        .getElementById("predict-btn")
        .addEventListener("click", function () {
            const inputValue = document.getElementById("land-area").value;

            let landArea = parseFloat(inputValue);

            if (inputValue === null || inputValue.trim() === "" || isNaN(landArea) || landArea <= 0) {
                landArea = 1;
            }

            fetch(`/run-model?land_area=${landArea}`)
                .then((response) => response.json())
                .then((data) => {
                    if (data.error) {
                        console.log("Error: " + data.error);
                        // Hide result card if error
                        alert("No Previous Data")
                        document
                            .getElementById("result-display")
                            .classList.add("hidden");
                    } else {
                        // Hide the default message
                        document.querySelector(
                            "#results > .text-gray-500"
                        ).style.display = "none";
                        // Show the result card
                        document
                            .getElementById("result-display")
                            .classList.remove("hidden");
                        // Update the price
                        document.querySelector(
                            ".price-display"
                        ).textContent = `$${Number(data.price).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
                        // document.querySelector(
                        //     "#price-per-m2"
                        // ).textContent = `$${data.price_per_m2.toLocaleString()}`;
                        // document.getElementById(
                        //     "price-range"
                        // ).textContent = `$${Math.round(
                        //     data.price_range[0]
                        // ).toLocaleString()} - $${Math.round(
                        //     data.price_range[1]
                        // ).toLocaleString()}`;
                        // document.querySelector(
                        //     "#land-area-show"
                        // ).innerHTML = `${data.land_area.toLocaleString()} m<sup>2</sup>`;
                        // Optionally update other fields if your backend returns them
                        // document.querySelector('.confidence-badge').textContent = data.confidence ? `${data.confidence}% Confidence` : '';
                        // etc.
                    }
                })
                .catch(() => {
                    document.getElementById("result").textContent =
                        "Prediction failed.";
                    document
                        .getElementById("result-display")
                        .classList.add("hidden");
                });
        });
});

document
    .getElementById("get-location")
    .addEventListener("click", function () {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function (position) {
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;

                    // Set the input fields
                    document.getElementById("latitude").value = lat.toFixed(6);
                    document.getElementById("longitude").value = lng.toFixed(6);

                    // Store coordinates in backend
                    fetch("/store-coord", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({
                            latitude: lat,
                            longitude: lng,
                        }),
                    });

                    // Get the iframe and send message
                    const mapFrame = document.querySelector("#map iframe");
                    if (mapFrame && mapFrame.contentWindow) {
                        mapFrame.contentWindow.postMessage(
                            {
                                type: "moveToLocation",
                                lat: lat,
                                lng: lng,
                            },
                            "*"
                        );
                    } else {
                        console.error("Could not find map iframe");
                    }
                },
                function (error) {
                    console.error("Geolocation error:", error);
                    alert("Could not get your location. Error: " + error.message);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 5000,
                    maximumAge: 0,
                }
            );
        } else {
            alert("Geolocation is not supported by this browser.");
        }
    });

document
    .getElementById("detail-btn")
    .addEventListener("click", function () {
        window.location.href = "/detail";
    });
document.getElementById("upload-file").addEventListener("click", () => {
    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.accept = ".csv";
    fileInput.style.display = "none";

    fileInput.addEventListener("change", async (event) => {
        const file = event.target.files[0];
        if (!file) return;
        const loadingSpinner = document.createElement("div");
        loadingSpinner.className =
            "fixed inset-0 flex items-center justify-center z-50 bg-black bg-opacity-50";
        loadingSpinner.innerHTML = `
          <div class="flex items-center justify-center w-56 h-56 border border-gray-200 rounded-lg bg-gray-50 dark:bg-gray-800 dark:border-gray-700">
              <div role="status">
                  <svg aria-hidden="true" class="w-8 h-8 text-gray-200 animate-spin dark:text-gray-600 fill-blue-600" viewBox="0 0 100 101" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z" fill="currentColor"/><path d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z" fill="currentFill"/></svg>
                  <span class="sr-only">Loading...</span>
              </div>
          </div>
          `;
        document.body.appendChild(loadingSpinner);
        document.body.style.overflow = "hidden"; // Prevent scrolling

        // Read CSV and convert to JSON
        const text = await file.text();
        const rows = text.split("\n").map((row) => row.split(","));

        // Send to Flask as JSON
        try {
            const response = await fetch("/upload", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json", // Required for Flask
                },
                body: JSON.stringify({ csvData: rows }), // Send parsed data
            });

            const result = await response.json();
            console.log("Success:", result);
            document.body.removeChild(loadingSpinner);
            document.body.style.overflow = "";

            const modal = document.getElementById("popup-modal");

            // Remove 'hidden' class to display the modal
            modal.classList.remove("hidden");
            document
                .querySelectorAll('[data-modal-hide="popup-modal"]')
                .forEach((btn) => {
                    btn.addEventListener("click", () => {
                        modal.classList.add("hidden");
                    });
                });
            document
                .getElementById("view-batch")
                .addEventListener("click", function () {
                    window.location.href = "/batch_detail";
                });
        } catch (error) {
            console.error("Error:", error);
        }
    });

    fileInput.click();
});
document.addEventListener("DOMContentLoaded", function () {
    const latitudeInput = document.getElementById("latitude");
    let lastValue = latitudeInput.value;

    setInterval(() => {
        if (latitudeInput.value !== lastValue) {
            lastValue = latitudeInput.value;
            // alert(1);
            fetchData();
        }
    }, 200); // check every 200ms
});
const featuresModule = (() => {
    let features = null;
    let isInitialLoad = true;

    return {
        getFeatures: () => features,
        setFeatures: (value) => {
            features = value;
            isInitialLoad = false;
        },
        isInitialLoad: () => isInitialLoad
    };
})();

function fetchData() {
    const old_data = featuresModule.getFeatures();

    fetch("/get-features")
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(new_data => {
            // Always log on initial load
            if (featuresModule.isInitialLoad()) {
                console.log('Initial data:', new_data);
                featuresModule.setFeatures(new_data);
                return;
            }
            // Log only if data changed
            if (!isEqual(old_data, new_data)) {
                console.log('Old data:', old_data);
                console.log('New data:', new_data);
                featuresModule.setFeatures(new_data);
                document.querySelector(
                    "#city-show"
                ).innerHTML = `<i class="fas fa-city text-primary"></i>
                ${new_data.address_subdivision.toLocaleString()}`;
                document.querySelector(
                    "#district-show"
                ).innerHTML = `<i class="fas fa-map-marker-alt text-primary"></i>
                ${new_data.address_locality.toLocaleString()}`;
                document.querySelector(
                    "#commune-show"
                ).innerHTML = `<i class="fas fa-home text-primary"></i>
                ${new_data.address_line_2.toLocaleString()}`;
            }
        })
        .catch(error => {
            console.error('Fetch error:', error);
            setTimeout(fetchData, 2000);
        });
}
function isEqual(obj1, obj2) {
    if (obj1 == null || obj2 == null) {
        return obj1 === obj2;
    }
    return JSON.stringify(obj1) === JSON.stringify(obj2);
}

fetchData();

function generatePdfReport() {
    // Show loading state
    const button = event.currentTarget;
    const originalContent = button.innerHTML;
    button.innerHTML =
        '<i class="fas fa-spinner fa-spin text-primary text-xl mb-2"></i><span class="text-sm">Generating...</span>';
    button.disabled = true;

    // Fetch the PDF from your Flask endpoint
    fetch("/generate-report")
        .then((response) => {
            if (!response.ok) {
                throw new Error("Network response was not ok");
            }
            return response.blob();
        })
        .then((blob) => {
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "Property_Valuation_Report.pdf";
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        })
        .catch((error) => {
            console.error("Error generating PDF:", error);
            alert("Failed to generate PDF report. Please try again.");
        })
        .finally(() => {
            // Restore button state
            button.innerHTML = originalContent;
            button.disabled = false;
        });
}
// setInterval(fetchData, 1000);
// fetch("/get-features")
//     .then((response) => response.json())
//     .then((data) => {
//         function setDropdown(selectId, value, labelPrefix) {
//             var select = window.parent.document.getElementById(selectId);
//             if (select) {
//                 select.innerHTML = "";
//                 var defaultOption = document.createElement("option");
//                 defaultOption.selected = true;
//                 defaultOption.disabled = true;
//                 defaultOption.textContent = "Choose a " + labelPrefix;
//                 select.appendChild(defaultOption);
//                 // Add the new value as an option and select it
//                 if (value) {
//                     var opt = document.createElement("option");
//                     opt.value = value;
//                     opt.textContent = value;
//                     opt.selected = true;
//                     select.appendChild(opt);
//                 }
//             }
//         }
//     });
// console.log(data);