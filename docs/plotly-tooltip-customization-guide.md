# Plotly Tooltip Customization Guide

This guide explains how to customize Plotly chart tooltips in your Financial Bubble Detection Dashboard, including dark mode support and advanced styling techniques.

## Overview

Your dashboard now includes enhanced dark mode-friendly tooltips with:
- Automatic theme switching based on your app's theme
- Enhanced visual styling with emojis and colors
- Better typography and spacing
- Smooth animations and transitions
- Responsive design for mobile devices

## Files Modified

1. **`src/styles/plotly-chart.css`** - Main tooltip styling
2. **`src/styles.css`** - Import statement added
3. **`src/components/PlotlyBubbleChart.tsx`** - Enhanced tooltip templates

## CSS Customization

### Theme Variables

The tooltip styling uses CSS custom properties that automatically adapt to light/dark themes:

```css
/* Light mode variables */
:root {
  --tooltip-bg: rgba(255, 255, 255, 0.95);
  --tooltip-border: #ccc;
  --tooltip-color: #333;
  --tooltip-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Dark mode variables */
[data-theme="dark"] {
  --tooltip-bg: rgba(30, 30, 30, 0.95);
  --tooltip-border: #555;
  --tooltip-color: #e0e0e0;
  --tooltip-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}
```

### Key Styling Classes

- `.plotly-chart-container .hoverlayer .hovertext` - Main tooltip container
- `.plotly-chart-container .hoverlayer .hovertext path` - Tooltip arrow/pointer
- `.plotly-chart-container .hoverlayer .hovertext .name` - Tooltip title
- `.plotly-chart-container .hoverlayer .hovertext b` - Bold text styling
- `.plotly-chart-container .hoverlayer .hovertext .value` - Numeric values

## Tooltip Template Customization

### Basic Structure

Plotly tooltips use HTML-like templates with special placeholders:

```javascript
hovertemplate: 
  "<b>%{fullData.name}</b><br>" +
  "Date: %{x|%B %d, %Y}<br>" +
  "Value: %{y:.3f}<br>" +
  "<extra></extra>"
```

### Available Placeholders

- `%{x}` - X-axis value
- `%{y}` - Y-axis value
- `%{z}` - Z-axis value (for 3D plots)
- `%{text}` - Text values
- `%{customdata[0]}` - First custom data value
- `%{fullData.name}` - Trace name
- `<extra></extra>` - Removes the default trace box

### Formatting Options

#### Date Formatting
```javascript
"%{x|%B %d, %Y}"     // January 15, 2024
"%{x|%m/%d/%Y}"      // 01/15/2024
"%{x|%Y-%m-%d}"      // 2024-01-15
```

#### Number Formatting
```javascript
"%{y:.2f}"           // 2 decimal places: 123.45
"%{y:.4f}"           // 4 decimal places: 123.4567
"%{y:,.0f}"          // Thousands separator: 1,234
"%{y:$,.2f}"         // Currency: $1,234.56
"%{y:.2%}"           // Percentage: 12.34%
```

## Advanced Customization Examples

### 1. Adding Custom Colors and Emojis

```javascript
hovertemplate:
  "<b style='font-size: 14px; color: #3b82f6;'>🔵 %{fullData.name}</b><br>" +
  "<span style='color: #6b7280;'>📅 Date:</span> <b>%{x|%B %d, %Y}</b><br>" +
  "<span style='color: #6b7280;'>📊 Value:</span> <b>%{y:.4f}</b><br>" +
  "<extra></extra>"
```

### 2. Multi-line Information with Custom Data

```javascript
// In your trace definition
customdata: data.map(d => [d.lowerBound, d.upperBound, d.confidence]),

hovertemplate:
  "<b>%{fullData.name}</b><br>" +
  "Date: %{x|%B %d, %Y}<br>" +
  "Estimate: %{y:.4f}<br>" +
  "Range: [%{customdata[0]:.4f}, %{customdata[1]:.4f}]<br>" +
  "Confidence: %{customdata[2]:.1%}<br>" +
  "<extra></extra>"
```

### 3. Conditional Styling

```javascript
hovertemplate:
  "<b style='color: %{marker.color};'>%{fullData.name}</b><br>" +
  "Value: <span style='font-weight: bold; color: %{y > 0 ? 'green' : 'red'};'>%{y:.3f}</span><br>" +
  "<extra></extra>"
```

## CSS Customization Examples

### 1. Changing Tooltip Appearance

```css
/* Larger, more rounded tooltips */
.plotly-chart-container .hoverlayer .hovertext {
  border-radius: 12px !important;
  padding: 16px 20px !important;
  font-size: 14px !important;
  min-width: 250px !important;
}
```

### 2. Custom Animation

```css
/* Bounce animation */
@keyframes tooltipBounce {
  0% { transform: scale(0.8) translateY(10px); opacity: 0; }
  50% { transform: scale(1.05) translateY(-2px); opacity: 0.8; }
  100% { transform: scale(1) translateY(0); opacity: 1; }
}

.plotly-chart-container .hoverlayer .hovertext {
  animation: tooltipBounce 0.3s ease-out !important;
}
```

### 3. Theme-Specific Styling

```css
/* Light theme specific */
:root .plotly-chart-container .hoverlayer .hovertext {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1) !important;
}

/* Dark theme specific */
[data-theme="dark"] .plotly-chart-container .hoverlayer .hovertext {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.6) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
}
```

## Responsive Design

The tooltips automatically adapt to different screen sizes:

```css
@media (max-width: 768px) {
  .plotly-chart-container .hoverlayer .hovertext {
    font-size: 12px !important;
    padding: 10px 14px !important;
    max-width: 250px !important;
  }
}
```

## Accessibility Features

The styling includes accessibility improvements:

- High contrast mode support
- Reduced motion support for users with vestibular disorders
- Proper color contrast ratios
- Screen reader friendly markup

## Testing Your Changes

1. **Theme Switching**: Toggle between light and dark modes to ensure tooltips adapt correctly
2. **Responsive Design**: Test on different screen sizes
3. **Accessibility**: Test with high contrast mode and reduced motion preferences
4. **Performance**: Ensure animations don't cause performance issues

## Common Issues and Solutions

### Issue: Tooltips not showing custom styles
**Solution**: Ensure the `plotly-chart-container` class is applied to the Plot component wrapper.

### Issue: Dark mode colors not applying
**Solution**: Check that your theme provider is correctly setting the `data-theme="dark"` attribute on the root element.

### Issue: Animations causing performance issues
**Solution**: Use `@media (prefers-reduced-motion: reduce)` to disable animations for users who prefer reduced motion.

## Next Steps

- Experiment with different color schemes
- Add more interactive elements to tooltips
- Consider adding custom tooltip positioning
- Explore Plotly's event system for advanced interactions

For more advanced customization, refer to the [Plotly.js documentation](https://plotly.com/javascript/hover-text-and-formatting/).
