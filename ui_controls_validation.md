# UI Controls & Validation Rules for EA Parameters

## 🔵 BINARY/BOOLEAN PARAMETERS

### **Recommended UI Controls:**
- **Toggle Switches** (modern, visual on/off state)
- **Checkboxes** (traditional, compact)
- **Grouped in collapsible sections** by feature area

### **Implementation Examples:**
```html
<!-- Toggle Switch Style -->
<div class="toggle-group">
  <label class="toggle">
    <input type="checkbox" id="use_trailing_stop">
    <span class="slider"></span>
    <span class="label">Use Trailing Stop</span>
  </label>
  <span class="help-icon" title="Enable automatic trailing stop functionality">ℹ️</span>
</div>

<!-- Checkbox Style -->
<label class="checkbox-control">
  <input type="checkbox" id="emergency_close_all_trades">
  <span class="checkmark"></span>
  Emergency Close All Trades
</label>
```

### **Validation Rules:**
- **No validation needed** (true/false inherently valid)
- **Dependency checks:** Some parameters only active when parent is enabled
- **Visual feedback:** Disabled appearance when dependent parameter is off

### **UX Enhancements:**
- **Grouped sections:** "Trailing Stop Options" collapses when `use_trailing_stop = false`
- **Smart defaults:** Safe conservative settings
- **Confirmation dialogs:** For destructive options like `emergency_close_all_trades`

---

## 🔢 NUMERIC PARAMETERS

### **Recommended UI Controls:**
- **Number Input Fields** with spinners
- **Range Sliders** for bounded values
- **Dual controls** (slider + input) for precision

### **Control Types by Parameter:**

#### **Percentage Values (0-100%)**
```html
<div class="range-control">
  <label>Global Risk Percent</label>
  <input type="range" min="0.1" max="10.0" step="0.1" value="1.0" id="risk_slider">
  <input type="number" min="0.1" max="10.0" step="0.1" value="1.0" id="risk_input">
  <span class="unit">%</span>
</div>
```

#### **Pip Values (1-500 range)**
```html
<div class="pip-control">
  <label>Stop Loss Pips</label>
  <input type="number" min="5" max="500" step="1" value="20" id="stop_loss_pips">
  <span class="unit">pips</span>
  <div class="validation-message"></div>
</div>
```

#### **Time Values (seconds/minutes)**
```html
<div class="time-control">
  <label>Entry Delay</label>
  <input type="number" min="0" max="300" step="1" value="0" id="entry_delay">
  <select id="time_unit">
    <option value="seconds">seconds</option>
    <option value="minutes">minutes</option>
  </select>
</div>
```

### **Validation Rules:**

#### **Risk Management Parameters**
```javascript
const validationRules = {
  global_risk_percent: {
    min: 0.1,
    max: 10.0,
    step: 0.1,
    warning: "Risk above 5% is extremely aggressive",
    error: "Risk must be between 0.1% and 10%"
  },
  
  stop_loss_pips: {
    min: 5,
    max: 500,
    step: 1,
    warning: "SL below 10 pips may cause frequent stops",
    error: "Stop loss must be between 5 and 500 pips"
  },
  
  risk_reward_ratio: {
    min: 0.5,
    max: 10.0,
    step: 0.1,
    warning: "RR below 1.5 may not be profitable long-term",
    error: "Risk-reward ratio must be between 0.5 and 10"
  }
}
```

#### **Relationship Validation**
```javascript
// Ensure TP > SL when using fixed values
function validateStopTakeProfit() {
  const sl = document.getElementById('stop_loss_pips').value;
  const tp = document.getElementById('take_profit_pips').value;
  
  if (tp <= sl) {
    showError("Take profit must be greater than stop loss");
    return false;
  }
  return true;
}

// Trailing stop cannot be larger than initial SL
function validateTrailingStop() {
  const sl = document.getElementById('stop_loss_pips').value;
  const trail = document.getElementById('trailing_stop_pips').value;
  
  if (trail >= sl) {
    showWarning("Trailing stop should be smaller than initial stop loss");
  }
}
```

#### **Real-time Validation**
```javascript
// Input validation with immediate feedback
function setupRealtimeValidation() {
  document.querySelectorAll('input[type="number"]').forEach(input => {
    input.addEventListener('blur', validateInput);
    input.addEventListener('input', debounce(validateInput, 500));
  });
}

function validateInput(event) {
  const input = event.target;
  const rules = validationRules[input.id];
  const value = parseFloat(input.value);
  
  // Clear previous validation
  input.classList.remove('error', 'warning');
  
  // Range validation
  if (value < rules.min || value > rules.max) {
    input.classList.add('error');
    showMessage(rules.error, 'error');
    return false;
  }
  
  // Warning thresholds
  if (rules.warning && shouldShowWarning(input.id, value)) {
    input.classList.add('warning');
    showMessage(rules.warning, 'warning');
  }
  
  return true;
}
```

---

## 📋 CHOICE/ENUM PARAMETERS

### **Recommended UI Controls:**

#### **Primary Choices (3-4 options)**
```html
<!-- Radio Button Group -->
<div class="radio-group">
  <legend>Entry Order Type</legend>
  <label class="radio-option">
    <input type="radio" name="entry_order_type" value="MARKET">
    <span class="radio-mark"></span>
    <div class="option-content">
      <strong>Market</strong>
      <small>Immediate execution at current price</small>
    </div>
  </label>
  
  <label class="radio-option">
    <input type="radio" name="entry_order_type" value="PENDING">
    <span class="radio-mark"></span>
    <div class="option-content">
      <strong>Pending</strong>
      <small>Place orders above/below current price</small>
    </div>
  </label>
  
  <label class="radio-option">
    <input type="radio" name="entry_order_type" value="STRADDLE">
    <span class="radio-mark"></span>
    <div class="option-content">
      <strong>Straddle</strong>
      <small>Place both buy and sell pending orders</small>
    </div>
  </label>
</div>
```

#### **Technical Choices (2-3 options)**
```html
<!-- Dropdown for technical parameters -->
<div class="select-control">
  <label for="stop_loss_method">Stop Loss Method</label>
  <select id="stop_loss_method" class="styled-select">
    <option value="FIXED">Fixed Pips</option>
    <option value="ATR_MULTIPLE">ATR Multiple</option>
    <option value="PERCENT">Percentage</option>
  </select>
  <div class="method-description">
    <span id="method_help">Choose how stop loss distance is calculated</span>
  </div>
</div>
```

#### **State Parameters (Visual Status)**
```html
<!-- Status indicator with dropdown -->
<div class="status-control">
  <label>EA State</label>
  <div class="status-wrapper">
    <div class="status-indicator" id="state_indicator"></div>
    <select id="current_ea_state">
      <option value="IDLE">Idle - Ready to trade</option>
      <option value="ORDERS_PLACED">Orders Placed - Waiting for trigger</option>
      <option value="TRADE_TRIGGERED">Trade Active - Managing position</option>
      <option value="DISABLED">Disabled - No trading activity</option>
    </select>
  </div>
</div>
```

### **Dynamic UI Behavior:**
```javascript
// Show/hide parameters based on selection
document.getElementById('entry_order_type').addEventListener('change', function(e) {
  const selectedType = e.target.value;
  
  // Hide all conditional sections
  document.querySelectorAll('.conditional-section').forEach(section => {
    section.style.display = 'none';
  });
  
  // Show relevant sections
  switch(selectedType) {
    case 'MARKET':
      document.getElementById('market-options').style.display = 'block';
      break;
    case 'PENDING':
      document.getElementById('pending-options').style.display = 'block';
      break;
    case 'STRADDLE':
      document.getElementById('straddle-options').style.display = 'block';
      break;
  }
});

// Update help text based on selection
document.getElementById('stop_loss_method').addEventListener('change', function(e) {
  const helpTexts = {
    'FIXED': 'Stop loss set at fixed pip distance from entry',
    'ATR_MULTIPLE': 'Stop loss based on Average True Range volatility',
    'PERCENT': 'Stop loss as percentage of entry price'
  };
  
  document.getElementById('method_help').textContent = helpTexts[e.target.value];
});
```

---

## 📝 STRING/TEXT PARAMETERS

### **Recommended UI Controls:**

#### **Identifier Fields**
```html
<div class="text-control">
  <label for="parameter_set_id">Parameter Set ID</label>
  <input type="text" 
         id="parameter_set_id" 
         placeholder="PS_001" 
         pattern="[A-Z]{2}_[0-9]{3}"
         maxlength="6"
         required>
  <div class="format-hint">Format: PS_001 (2 letters, underscore, 3 digits)</div>
</div>
```

#### **Complex Configuration Strings**
```html
<div class="config-control">
  <label for="partial_tp_levels">Partial Take Profit Levels</label>
  <input type="text" 
         id="partial_tp_levels" 
         placeholder="50|75|90"
         pattern="[0-9]+(\|[0-9]+)*">
  <div class="format-hint">
    Enter percentages separated by | (pipe). Example: 50|75|90
  </div>
  <button type="button" class="helper-btn" onclick="openTPHelper()">
    Configure Visually
  </button>
</div>

<!-- Visual helper modal -->
<div id="tp-helper-modal" class="modal">
  <div class="tp-levels">
    <div class="level-input">
      <label>Level 1:</label>
      <input type="number" min="10" max="90" value="50"> %
    </div>
    <div class="level-input">
      <label>Level 2:</label>
      <input type="number" min="10" max="90" value="75"> %
    </div>
    <button onclick="addTPLevel()">Add Level</button>
  </div>
</div>
```

### **Validation Rules:**
```javascript
const stringValidation = {
  parameter_set_id: {
    pattern: /^[A-Z]{2}_[0-9]{3}$/,
    maxLength: 6,
    required: true,
    error: "Must follow format: PS_001 (2 uppercase letters, underscore, 3 digits)"
  },
  
  name: {
    maxLength: 50,
    pattern: /^[A-Za-z0-9_\- ]+$/,
    required: true,
    error: "Name can only contain letters, numbers, spaces, hyphens, and underscores"
  },
  
  partial_tp_levels: {
    pattern: /^[0-9]+(\|[0-9]+)*$/,
    validator: function(value) {
      const levels = value.split('|').map(Number);
      return levels.every(level => level > 0 && level < 100) &&
             levels.every((level, i) => i === 0 || level > levels[i-1]);
    },
    error: "Must be ascending percentages separated by |. Example: 25|50|75"
  },
  
  bias_override_by_category: {
    pattern: /^(CAT[0-9]+=[-]?[01](\|CAT[0-9]+=[-]?[01])*)?$/,
    error: "Format: CAT1=-1|CAT2=0 (categories with bias values -1, 0, or 1)"
  }
};
```

---

## 🎨 ADVANCED UI ENHANCEMENTS

### **Parameter Grouping & Layout**
```html
<div class="parameter-groups">
  <!-- Collapsible sections -->
  <div class="param-group" data-group="required">
    <div class="group-header" onclick="toggleGroup('required')">
      <h3>Required Parameters</h3>
      <span class="expand-icon">▼</span>
    </div>
    <div class="group-content">
      <!-- Parameters here -->
    </div>
  </div>
  
  <div class="param-group" data-group="risk">
    <div class="group-header" onclick="toggleGroup('risk')">
      <h3>Risk Management</h3>
      <span class="expand-icon">▼</span>
    </div>
    <div class="group-content">
      <!-- Risk parameters -->
    </div>
  </div>
</div>
```

### **Real-time Preview**
```javascript
// Live parameter preview
function createParameterPreview() {
  const preview = {
    calculateRisk: function() {
      const riskPercent = document.getElementById('global_risk_percent').value;
      const stopLoss = document.getElementById('stop_loss_pips').value;
      const accountBalance = 10000; // Example
      
      const riskAmount = accountBalance * (riskPercent / 100);
      const lotSize = riskAmount / (stopLoss * 10); // Simplified calculation
      
      document.getElementById('risk_preview').innerHTML = `
        <strong>Risk Preview:</strong><br>
        Risk Amount: $${riskAmount.toFixed(2)}<br>
        Suggested Lot Size: ${lotSize.toFixed(2)}
      `;
    }
  };
  
  // Update preview on parameter changes
  document.querySelectorAll('.risk-param').forEach(input => {
    input.addEventListener('input', preview.calculateRisk);
  });
}
```

### **Parameter Validation Summary**
```html
<div class="validation-summary">
  <div class="summary-header">
    <h4>Configuration Status</h4>
    <div class="status-indicator" id="overall_status"></div>
  </div>
  
  <div class="validation-items">
    <div class="validation-item valid">
      <span class="check">✓</span>
      Required parameters complete
    </div>
    <div class="validation-item warning">
      <span class="warning">⚠</span>
      High risk settings detected
    </div>
    <div class="validation-item error">
      <span class="error">✗</span>
      Take profit must be greater than stop loss
    </div>
  </div>
</div>
```

This comprehensive UI design ensures users can configure parameters safely while preventing common errors through real-time validation and helpful visual feedback.