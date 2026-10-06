---
name: PhishX
description: A calm local workspace for inspecting URL risk and its explanation.
colors:
  primary: "#234e37"
  primary-hover: "#153b29"
  background: "#f5f5ef"
  foreground: "#233b33"
  surface: "#ffffff"
  border: "#c9d0c3"
  muted: "#55665c"
  supporting-text: "#506158"
  focus: "#a46520"
  input-background: "#fcfdf9"
  input-border: "#8d9e91"
  placeholder: "#617366"
  badge-background: "#e4e9dc"
  badge-text: "#43594f"
  notice-background: "#f2efd9"
  notice-text: "#5c4b23"
  example-background: "#eff3e8"
  example-border: "#d4ddca"
  example-hover: "#dde8ce"
  divider: "#dce2d4"
  code-background: "#e7eddf"
  error: "#9a2d27"
  error-background: "#fff0ec"
  risk-low: "#275735"
  risk-medium: "#746119"
  risk-high: "#8b4711"
  risk-critical: "#a2322b"
typography:
  display:
    fontFamily: "Georgia, serif"
    fontSize: "clamp(38px, 4.7vw, 58px)"
    fontWeight: 400
    lineHeight: 1.08
    letterSpacing: "-.03em"
  title:
    fontFamily: "Segoe UI, sans-serif"
    fontSize: "21px"
    fontWeight: 650
    lineHeight: 1.3
  body:
    fontFamily: "Segoe UI, sans-serif"
    lineHeight: 1.6
  label:
    fontFamily: "Segoe UI, sans-serif"
    fontSize: "14px"
    fontWeight: 650
  mono:
    fontFamily: "Consolas, monospace"
    fontSize: "15px"
rounded:
  example: "5px"
  control: "6px"
  code: "8px"
  scanner: "14px"
  badge: "30px"
spacing:
  label-gap: "8px"
  section-gap: "20px"
  mobile-panel: "22px"
  desktop-panel: "28px"
  column-gap: "36px"
  result-gap: "38px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    padding: "12px 18px"
    width: "100%"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-example:
    backgroundColor: "{colors.example-background}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.example}"
    padding: "6px 10px"
  input:
    backgroundColor: "{colors.input-background}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.control}"
    padding: "13px 14px"
    width: "100%"
  scanner:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.scanner}"
    padding: "28px"
  prototype-badge:
    backgroundColor: "{colors.badge-background}"
    textColor: "{colors.badge-text}"
    rounded: "{rounded.badge}"
    padding: "5px 12px"
  notice:
    backgroundColor: "{colors.notice-background}"
    textColor: "{colors.notice-text}"
    rounded: "{rounded.control}"
    padding: "12px 15px"
---

# Design System: PhishX

## Overview

**Creative North Star: "The Calm Scanner Workspace"**

The implemented direction is a functional light workspace with a green primary action, a serif task heading, and readable system sans text. The form carries the action; quieter supporting content explains its scope and the results carry the evidence. This name describes the established direction rather than claiming a separate brand workshop.

The system uses compact controls inside a generous page rhythm. Notices and textual status labels keep prototype and fixture limitations visible. No external fonts or brand imagery are required.

**Key Characteristics:**
- Calm light surfaces and dark green action emphasis.
- Serif task heading paired with system sans interface text.
- Bordered, flat containers and visible keyboard focus.
- Explicit result labels and a mobile reading order that follows the task.

## Colors

Green anchors the action palette; warm pale backgrounds and subdued text keep the workspace quiet. Frontmatter values are normative.

### Primary
- **Forest Green:** the analyze action and text caret; deeper green marks enabled hover.

### Neutral
- **Warm Paper / White Surface:** the page and scanner panel respectively.
- **Deep Green Ink / Muted Green Gray:** primary content and supporting instructions.
- **Sage Borders:** panel outlines, fields, and separating rows.
- **Pale Sage:** example buttons, prototype badge, and response code background.

### Semantic colors
- **Amber Focus:** keyboard outlines on buttons, links, inputs, and disclosure summaries.
- **Warm Notice:** fixture and backend notices.
- **Brick Error:** a failed request, with a pale error surface.
- **Risk colors:** green, muted ochre, brown, and red accompany low through critical text labels.

**The Labeled State Rule.** Color accompanies a written state or risk label; it never carries the meaning alone.

## Typography

**Display Font:** Georgia with serif fallback.
**Body Font:** Segoe UI with sans-serif fallback.
**Label/Mono Font:** Consolas with monospace fallback for hosts and model feature values.

The serif heading adds a measured editorial tone to an otherwise practical interface. System fonts keep the local prototype self-contained.

### Hierarchy
- **Display:** the task heading uses the frontmatter display role.
- **Title:** section headings use the title role; subsection headings are smaller (17px), semibold (650).
- **Body:** inherits a comfortable line height; intro copy is larger (17px) with a narrow reading measure (44ch desktop, 60ch mobile).
- **Label:** field labels use the label role; hints and metadata step down (13px), examples and footer down again (12px).
- **Mono:** hosts use the mono role; contribution metadata and raw JSON are smaller (12px).
- **Score:** tabular numerals are large (38px desktop, 32px mobile), with a quieter denominator.

**The Task Heading Rule.** Reserve the serif display treatment for the primary task heading; use sans-serif for controls and evidence headings.

## Layout

The centered shell has a maximum width (1160px), desktop horizontal padding (36px), and top padding (32px). The introduction uses an asymmetric two-column layout (1.1:1). The scanner and scope use a wider action column (1.65:1) with a gap (36px); the results repeat that proportion with a slightly wider gap (40px).

At the mobile breakpoint (760px), the introduction, workspace, and result grid stack in DOM reading order. Shell padding becomes (22px 20px), scanner padding becomes (22px), and column gaps become (20px). Results sit below the workspace; an empty-state divider occupies the same position before analysis. Long hosts and feature values wrap; raw JSON scrolls within its own container.

## Elevation & Depth

There are no box shadows. Depth comes from white and pale tonal surfaces, thin borders, and horizontal separators. The scanner is the strongest bounded surface; scope and results remain part of the page rather than becoming floating cards.

**The Flat Surface Rule.** Preserve tonal separation and borders as the depth vocabulary.

## Shapes

The scanner has gently curved corners using the scanner radius. Inputs, action buttons, notices, and errors share the control radius. Smaller example buttons use the example radius, while the prototype badge is pill-shaped. Border strokes are thin (1px); shapes are restrained and tied to their function.

## Components

### Buttons

The primary action is confident and full width, with its label and arrow separated across the row. It uses the primary component tokens and a semibold label (600). Enabled hover darkens the green. Disabled buttons reduce opacity (.55) and use the not-allowed cursor. Keyboard focus uses an amber outline (3px) offset from the control (4px).

Example actions are compact outlined sage buttons, wrap across rows, and lighten the task of choosing fixture input. Hover changes their background. The retry action is an underlined inline button inside a notice.

### Cards / Containers

The white scanner has the scanner component tokens and a sage border. Internal headings align with status text; notices precede the form. Results use a top divider, with separate model contributions, observed signals, and unavailable signals. Scope remains unboxed.

### Inputs / Fields

The single URL field uses the input tokens and a sage stroke. Its text size (16px) remains readable on mobile. The label and format hint are always outside the field. Focus uses the shared outline, and busy state disables input while textual feedback appears. Errors use the semantic error surface below the form.

### Navigation

The home link pairs a shield/check SVG with a bold wordmark (25px, 750). The header has a bottom border and a separate prototype badge. This implementation has no multi-item navigation menu.

### Result and response disclosure

A right-aligned score pairs a tabular number with risk and sample labels. Host text uses monospace and wraps. The API response is a native disclosure containing bounded, scrolling JSON with a pale sage background. Under a no-preference motion setting, buttons transition background (150ms ease-out) and results reveal via clip-path (250ms ease-out); reduced-motion preference omits these effects.

## Do's and Don'ts

### Do:
- Do preserve the serif task heading and sans-serif controls.
- Do retain visible focus outlines and written status labels.
- Do stack task, scope, and results in their existing reading order on mobile.
- Do keep fixture notices and score qualification close to the relevant action or result.

### Don't:
- Don't use color as the only signal for risk, error, or readiness.
- Don't add shadow-driven card depth to this flat workspace without revisiting the visual direction.
- Don't style fixture scores as verified predictions.

<!-- Extracted from frontend/src/style.css and frontend/src/main.jsx. Review evidence: .impeccable/review/desktop.png and mobile.png; finish reviewer disposition: ship functional prototype, no material findings. Context launcher and detector engine were unavailable; no automated context/detector success is claimed. -->
