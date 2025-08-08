const priceModule = (() => {
    let price_show; // Private variable

    return {
        getPrice: () => price_show,
        setPrice: (value) => {
            price_show = value;
        },
    };
})();
const price_per_m2_Module = (() => {
    let price_show; // Private variable
    let min = 0;    // Default minimum
    let max = Infinity; // Default maximum

    return {
        getPrice: () => price_show,

        setPrice: (value) => {
            console.log("price: ", value);
            price_show = value;
        },

        setMin: (value) => {
            console.log("price min: ", value);
            min = value;
        },

        setMax: (value) => {
            console.log("price max: ", value);
            max = value;
        },

        getMin: () => min,
        getMax: () => max
    };
})();



fetch("/run-model")
    .then((response) => response.json())
    .then((data) => {
        // Use your data here
        console.log(data);
        priceModule.setPrice(data.price);
        price_per_m2_Module.setPrice(data.price_per_m2);
        document.querySelector(".price-display").textContent = `$${Math.trunc(
            data.price
        ).toLocaleString()}.00`;
        document.querySelector(".price_per_m2").textContent = `$${Math.trunc(
            data.price_per_m2
        ).toLocaleString()}.00`;
        document.querySelector(
            ".land_area"
        ).innerHTML = `${data.land_area.toLocaleString()} m<sup>2</sup>`;
        document.querySelector("#price-min").textContent = `$${Math.trunc(
            price_per_m2_Module.getMin()
        ).toLocaleString()}`;
        document.querySelector("#price-max").textContent = `$${Math.trunc(
            price_per_m2_Module.getMax()
        ).toLocaleString()}`;
    })
    .catch((error) => {
        console.error("Error fetching data:", error);
    });
fetch("/nearby-properties")
    .then((response) => response.json())
    .then((data) => {
        const count = data.count;
        nearby_data = data.results.nearby_properties;
        // console.log(nearby_data[1]);
        const total_price_per_m2 = nearby_data.reduce(
            (sum, currentItem) => sum + currentItem.price_per_m2,
            0
        );
        const avg_price_per_m2 = Math.trunc(total_price_per_m2 / count);
        const price_growth =
            ((price_per_m2_Module.getPrice() - avg_price_per_m2) / avg_price_per_m2) * 100;

        const highestItem = nearby_data.reduce((maxItem, currentItem) => {
            if (!maxItem || (currentItem.price_per_m2 || 0) > (maxItem.price_per_m2 || 0)) {
                return currentItem;
            }
            return maxItem;
        }, null);
        price_per_m2_Module.setMax(highestItem.price_per_m2);

        const lowestItem = nearby_data.reduce((minItem, currentItem) => {
            if (!minItem || (currentItem.price_per_m2 || 0) < (minItem.price_per_m2 || 0)) {
                return currentItem;
            }
            return minItem;
        }, null);
        price_per_m2_Module.setMin(lowestItem.price_per_m2);
        const low = price_per_m2_Module.getMin();
        const high = price_per_m2_Module.getMax();
        const estimate = price_per_m2_Module.getPrice();
        document.querySelector("#price-min").textContent = `$${Math.trunc(low).toLocaleString()}`;
        document.querySelector("#price-max").textContent = `$${Math.trunc(high).toLocaleString()}`;


        let widthPercent = 0;
        if (high !== low) {
            widthPercent = ((estimate - low) / (high - low)) * 100;
        }
        widthPercent = Math.min(Math.max(widthPercent, 0), 100);

        document.querySelector("#pipe").style.width = widthPercent + "%";


        console.log("Highest item by price_per_m2:", highestItem);
        document.querySelector(
            "#properties_sold"
        ).textContent = `${count.toLocaleString()}`;
        if (price_growth < 0) {
            const element = document.getElementById('price-growth');
            element.classList.remove('text-primary');
            element.classList.add('text-danger');
        }
        document.querySelector(
            "#price-growth"
        ).textContent = `${price_growth.toFixed(2).toLocaleString()}%`;
        document.querySelector(
            "#avg_price_per_m2"
        ).textContent = `$${avg_price_per_m2.toLocaleString()}`;
        document.querySelector(
            "#high_price"
        ).textContent = `$${Math.trunc(highestItem.price_per_m2).toLocaleString()}`;


    });
fetch("/nearby-properties")
    .then((response) => response.json())
    .then((data) => {
        const properties_container = document.getElementById(
            "properties-container"
        );
        const nearby_properties = data.results.nearby_properties;

        if (!properties_container) {
            console.error(
                "Error: '#properties-container' not found in the DOM."
            );
            return;
        }

        // Clear previous content
        properties_container.innerHTML = "";

        // Show first 3 properties initially
        const initialCount = 3;
        const showAll = nearby_properties.length <= initialCount;

        // Function to render properties
        const renderProperties = (propertiesToShow) => {
            propertiesToShow.forEach((property) => {
                const propertyHtml = `
          <div class="property-card bg-white rounded-lg p-4 border mb-4">
            <div class="flex justify-between items-start">
              <div>
                <p class="font-semibold">
                  ${property.address_line_2}, 
                  ${property.address_locality}, 
                  ${property.address_subdivision}
                </p>
                <p class="text-sm text-gray-600">
                  ${property.distance_km.toFixed(2)} km away
                </p>
              </div>
              <div class="text-right">
                <p class="font-bold text-lg text-warning">
                  $${Math.trunc(property.price).toLocaleString()}
                </p>
                <p class="text-sm">
                  $${Math.trunc(property.price_per_m2).toLocaleString()}/m²
                </p>
                <p class="text-sm">${property.land_area} m²</p>
              </div>
            </div>
           
          </div>
        `;
                properties_container.insertAdjacentHTML(
                    "beforeend",
                    propertyHtml
                );
            });
        };

        // Initial render (first 3 or all if <= 3)
        renderProperties(
            showAll
                ? nearby_properties
                : nearby_properties.slice(0, initialCount)
        );

        // Add "Show More" button if there are more properties
        if (!showAll) {
            const showMoreButtonHtml = `
        <button class="w-full mt-6 bg-gray-100 hover:bg-gray-200 text-gray-800 py-3 rounded-lg font-medium flex items-center justify-center transition-colors" id="showMorePropertiesBtn">
          <i class="fas fa-plus-circle mr-2"></i> Show More Properties (${nearby_properties.length - initialCount
                } more)
        </button>
      `;
            properties_container.insertAdjacentHTML(
                "beforeend",
                showMoreButtonHtml
            );

            // Add click handler
            document
                .getElementById("showMorePropertiesBtn")
                .addEventListener("click", () => {
                    // Remove the button
                    const button = document.getElementById("showMorePropertiesBtn");
                    if (button) button.remove();

                    // Render remaining properties
                    renderProperties(nearby_properties.slice(initialCount));
                });
        }
    })
    .catch((error) => {
        console.error("Error fetching nearby properties:", error);
    });
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

document.getElementById("save").addEventListener("click", function () {
    fetch("/last-prediction")
        .then((response) => response.json())
        .then((data) => {
            if (data.error) {
                alert(data.error);
                return;
            }

            // Send to backend to save
            fetch("/save-prediction", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            })
                .then((response) => response.json())
                .then((result) => {
                    window.location.href = result.redirect;
                })
                .catch((err) => {
                    console.error("Save failed:", err);
                    alert("Save failed.");
                });
        })
        .catch((err) => {
            console.error("Fetch failed:", err);
            alert("Could not fetch prediction data.");
        });
});