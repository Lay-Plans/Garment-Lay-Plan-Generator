document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ DOM loaded, initializing shirt pattern application");

  // Get DOM elements
  const categorySection = document.getElementById("category-section");
  const styleSection = document.getElementById("style-section");
  const measurementSection = document.getElementById("measurement-section");
  const outputSection = document.getElementById("pattern-output-section");
  const form = document.getElementById("measurement-form");
  const patternContainer = document.getElementById("pattern-svg");
  const patternTable = document.getElementById("pattern-table")?.querySelector("tbody");

  // Style configurations for shirts
  const styles = {
    tops: [
      { name: "Shirt", value: "shirt", img: "images/shirt.jpg" }
    ],
    bottoms: [],
    dresses: [],
    fullbody: []
  };

  const shirtStyles = [
    { name: "Dress Shirt", value: "dress_shirt", img: "images/dress-shirt.jpg" },
    { name: "Casual Shirt", value: "casual_shirt", img: "images/casual-shirt.jpg" }
  ];

  const fitTypes = [
    { name: "Slim Fit", value: "slim", description: "Close-fitting, minimal ease", img: "images/slim-fit.jpg" },
    { name: "Regular Fit", value: "regular", description: "Classic comfortable fit", img: "images/regular-fit.jpg" },
    { name: "Loose Fit", value: "loose", description: "Relaxed fit with extra ease", img: "images/loose-fit.jpg" }
  ];

  // Measurement fields for shirts (based on Seamly2D pattern requirements)
  const measurementFields = {
    shirt: [
      { key: "chest", label: "Chest Circumference", help: "Around fullest part of chest, arms at sides" },
      { key: "waist", label: "Waist Circumference", help: "Around natural waistline" },
      { key: "hip", label: "Hip Circumference", help: "Around fullest part of hips" },
      { key: "neck", label: "Neck Circumference", help: "Around base of neck where collar sits" },
      { key: "shoulder_length", label: "Shoulder Length", help: "From neck point to shoulder edge" },
      { key: "arm_length", label: "Arm Length", help: "From shoulder point to wrist bone" },
      { key: "back_length", label: "Back Length", help: "From prominent neck bone to waistline" },
      { key: "shirt_length", label: "Shirt Length", help: "From high point shoulder to desired hem" },
      { key: "bicep", label: "Bicep Circumference", help: "Around fullest part of upper arm" },
      { key: "wrist", label: "Wrist Circumference", help: "Around wrist bone" },
      { key: "armhole_depth", label: "Armhole Depth", help: "From shoulder point to underarm" }
    ]
  };

  // Utility functions
  function showLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.style.display = 'flex';
  }

  function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.style.display = 'none';
  }

  function showError(message) {
    const container = document.getElementById('error-container');
    const textElement = container?.querySelector('.error-text');
    if (container && textElement) {
      textElement.textContent = message;
      container.style.display = 'block';
    }
  }

  function showSuccess(message) {
    const container = document.getElementById('success-container');
    const textElement = container?.querySelector('.success-text');
    if (container && textElement) {
      textElement.textContent = message;
      container.style.display = 'block';
    }
  }

  function hideError() {
    const container = document.getElementById('error-container');
    if (container) container.style.display = 'none';
  }

  function hideSuccess() {
    const container = document.getElementById('success-container');
    if (container) container.style.display = 'none';
  }

  // Navigation functions
  function showSection(sectionToShow) {
    [categorySection, styleSection, measurementSection, outputSection].forEach(section => {
      if (section) section.style.display = 'none';
    });
    if (sectionToShow) sectionToShow.style.display = 'block';
  }

  function showStyles(category) {
    showSection(styleSection);
    const container = document.getElementById('style-options');
    if (!container) return;
    
    container.innerHTML = '';
    const categoryStyles = styles[category] || [];
    
    categoryStyles.forEach(style => {
      const div = document.createElement('div');
      div.className = 'style-container';
      
      const img = document.createElement('img');
      img.src = style.img;
      img.alt = style.name;
      img.className = 'style-image';
      img.onclick = () => {
        if (style.value === 'shirt') {
          showShirtSubStyles();
        } else {
          showMeasurements(style.value);
        }
      };
      
      const label = document.createElement('div');
      label.className = 'style-label';
      label.textContent = style.name;
      
      div.appendChild(img);
      div.appendChild(label);
      container.appendChild(div);
    });
  }

  function showShirtSubStyles() {
    const container = document.getElementById('style-options');
    if (!container) return;
    
    container.innerHTML = '';
    shirtStyles.forEach(style => {
      const div = document.createElement('div');
      div.className = 'style-container';
      
      const img = document.createElement('img');
      img.src = style.img;
      img.alt = style.name;
      img.className = 'style-image';
      img.onclick = () => showFitSelection(style.value);
      
      const label = document.createElement('div');
      label.className = 'style-label';
      label.textContent = style.name;
      
      div.appendChild(img);
      div.appendChild(label);
      container.appendChild(div);
    });
  }

  function showFitSelection(shirtStyle) {
    const container = document.getElementById('style-options');
    if (!container) return;
    
    container.innerHTML = '';
    
    // Add title
    const title = document.createElement('h3');
    title.textContent = 'Choose Your Fit';
    title.style.width = '100%';
    title.style.textAlign = 'center';
    title.style.marginBottom = '20px';
    container.appendChild(title);
    
    fitTypes.forEach(fit => {
      const div = document.createElement('div');
      div.className = 'style-container fit-container';
      
      const img = document.createElement('img');
      img.src = fit.img;
      img.alt = fit.name;
      img.className = 'style-image';
      img.onclick = () => showMeasurements(shirtStyle, fit.value);
      
      const label = document.createElement('div');
      label.className = 'style-label';
      label.innerHTML = `<strong>${fit.name}</strong><br><small>${fit.description}</small>`;
      
      div.appendChild(img);
      div.appendChild(label);
      container.appendChild(div);
    });
  }

  function showMeasurements(shirtStyle, fitType) {
    showSection(measurementSection);
    window.selectedStyle = shirtStyle;
    window.selectedFit = fitType;
    populateMeasurementFields();
  }

  function populateMeasurementFields() {
    const fieldContainer = document.getElementById("measurement-fields");
    if (!fieldContainer) return;
    
    fieldContainer.innerHTML = "";
    const fields = measurementFields.shirt || [];

    fields.forEach(field => {
      const div = document.createElement('div');
      div.className = 'measure';
      
      const label = document.createElement("label");
      label.setAttribute('for', field.key);
      label.innerHTML = `${field.label} (cm) ${field.help ? `<small class="help-text">- ${field.help}</small>` : ''}`;
      
      const input = document.createElement("input");
      input.type = "number";
      input.id = field.key;
      input.name = field.key;
      input.required = true;
      input.min = "1";
      input.step = "0.1";
      input.placeholder = "Enter measurement";
      
      div.appendChild(label);
      div.appendChild(input);
      fieldContainer.appendChild(div);
    });
  }

  // Set up category buttons
  const categoryButtons = document.querySelectorAll('.category-btn');
  categoryButtons.forEach((btn, index) => {
    const categories = ['tops', 'bottoms', 'dresses', 'fullbody'];
    btn.addEventListener('click', () => showStyles(categories[index]));
  });

  // Set up navigation buttons
  const setupNavButton = (selector, handler) => {
    const btn = document.querySelector(selector);
    if (btn) btn.addEventListener('click', handler);
  };

  setupNavButton('.nav-btn.secondary', () => showSection(categorySection));
  setupNavButton('#pattern-output-section .nav-btn.secondary', () => showSection(measurementSection));
  setupNavButton('#pattern-output-section .nav-btn.secondary:last-child', () => showSection(categorySection));

  // Set up error/success close buttons
  setupNavButton('.error-close', hideError);
  setupNavButton('.success-close', hideSuccess);

  // SINGLE form submission handler
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      
      try {
        showLoading();
        hideError();
        hideSuccess();

        console.log("🟡 Form submitted for shirt pattern generation");

        // Collect measurements
        const measurements = {};
        const inputs = document.querySelectorAll('#measurement-fields input');
        
        for (const input of inputs) {
          const value = parseFloat(input.value);
          if (isNaN(value) || value <= 0) {
            throw new Error(`Please enter a valid ${input.previousElementSibling.textContent.split('(')[0].trim()}`);
          }
          measurements[input.name] = value;
        }

        console.log("🟡 Sending measurements:", measurements);

        // Get customer name and style info
        const customerNameInput = document.getElementById('customer-name');
        const customerName = customerNameInput ? customerNameInput.value.trim() : 'Customer';
        
        const garmentStyle = window.selectedStyle === 'dress_shirt' ? "Men's Dress Shirt" : "Casual Shirt";
        const fitType = window.selectedFit || 'regular';

        // Make API call to Flask backend
        const response = await fetch("/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            measurements: measurements,
            user_name: customerName,
            garment_style: garmentStyle,
            fit_type: fitType
          })
        });

        console.log("🟡 Server responded with status:", response.status);

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.message || `Server error (${response.status})`);
        }

        const data = await response.json();
        console.log("🟢 Received from server:", data);

        if (data.status !== 'success') {
          throw new Error(data.message || 'Failed to generate pattern');
        }

        // Update pattern table
        if (patternTable && data.pattern_data) {
          patternTable.innerHTML = "";
          data.pattern_data.forEach(piece => {
            const row = document.createElement("tr");
            row.innerHTML = `
              <td>${piece['Pattern Piece'] || ''}</td>
              <td>${piece['Dimensions'] || ''}</td>
              <td>${piece['Cutting Notes'] || ''}</td>
              <td>${piece['Grainline'] || ''}</td>
              <td>${piece['Notches'] || ''}</td>
            `;
            patternTable.appendChild(row);
          });

          // Draw pattern visualization
          drawPatternVisualization(data.pattern_data, measurements);
        }

        // Set up download button
        const downloadBtn = document.getElementById('download-btn');
        if (downloadBtn && data.download_url) {
          downloadBtn.onclick = () => {
            window.open(data.download_url, '_blank');
          };
        }

        // Show output section
        showSection(outputSection);
        showSuccess(`${data.fit_type.charAt(0).toUpperCase() + data.fit_type.slice(1)} fit ${garmentStyle.toLowerCase()} pattern generated successfully!`);

        // Scroll to output
        setTimeout(() => {
          outputSection.scrollIntoView({ behavior: "smooth" });
        }, 100);

      } catch (error) {
        console.error("🔴 Error generating pattern:", error);
        showError(error.message || "There was an error generating the pattern. Please try again.");
      } finally {
        hideLoading();
      }
    });
  }

  // Pattern visualization function
  function drawPatternVisualization(patternData, measurements) {
    const svg = document.getElementById('pattern-svg');
    if (!svg) return;
    
    // Clear existing content except defs
    const defs = svg.querySelector('defs');
    svg.innerHTML = '';
    if (defs) svg.appendChild(defs);

    const scale = 1.5; // Scale factor for visualization
    let x = 20;
    let y = 20;
    let rowHeight = 0;

    patternData.forEach((piece, index) => {
      const dimensions = piece.Dimensions.split(' x ');
      const width = parseFloat(dimensions[0]) * scale;
      const height = parseFloat(dimensions[1]) * scale;

      // Check if we need to move to next row
      if (x + width + 10 > 1400) {
        x = 20;
        y += rowHeight + 40;
        rowHeight = 0;
      }

      // Color coding for different pattern pieces
      const colors = [
        "#e6f3ff", "#fff2e6", "#f0f8e6", "#ffeef0", 
        "#f0e6ff", "#e6fff0", "#fff0e6", "#e6f0ff",
        "#f8f0e6", "#e6f8ff"
      ];
      const fillColor = colors[index % colors.length];

      // Draw rectangle
      const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      rect.setAttribute("x", x);
      rect.setAttribute("y", y);
      rect.setAttribute("width", width);
      rect.setAttribute("height", height);
      rect.setAttribute("fill", fillColor);
      rect.setAttribute("stroke", "#333");
      rect.setAttribute("stroke-width", "1");
      rect.setAttribute("rx", "2"); // Rounded corners
      svg.appendChild(rect);

      // Add label
      const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
      label.setAttribute("x", x + 5);
      label.setAttribute("y", y - 5);
      label.setAttribute("font-size", "10");
      label.setAttribute("font-family", "Arial, sans-serif");
      label.setAttribute("font-weight", "bold");
      label.textContent = piece['Pattern Piece'];
      svg.appendChild(label);

      // Add dimensions text
      const dimText = document.createElementNS("http://www.w3.org/2000/svg", "text");
      dimText.setAttribute("x", x + 5);
      dimText.setAttribute("y", y + 15);
      dimText.setAttribute("font-size", "8");
      dimText.setAttribute("font-family", "Arial, sans-serif");
      dimText.setAttribute("fill", "#666");
      dimText.textContent = piece.Dimensions;
      svg.appendChild(dimText);

      x += width + 20;
      rowHeight = Math.max(rowHeight, height);
    });
  }

  // Add CSS for help text
  const style = document.createElement('style');
  style.textContent = `
    .help-text {
      color: #666;
      font-style: italic;
      display: block;
      margin-top: 2px;
    }
    .fit-container {
      margin: 10px;
      text-align: center;
    }
    .fit-container .style-label {
      padding: 10px;
    }
    .measure {
      margin-bottom: 20px;
    }
    .measure label {
      display: block;
      margin-bottom: 8px;
      font-weight: 600;
      line-height: 1.4;
    }
  `;
  document.head.appendChild(style);

  console.log("✅ Shirt pattern application initialized successfully");
});