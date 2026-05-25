/**
 * AI Taqdimot Ustasi — Ultra Premium PPTX Generator
 * 20+ unique slide layouts, real images via Unsplash, icon system
 */

const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const https = require("https");
const http = require("http");
const fs = require("fs");

// ─── Icon imports ─────────────────────────────────────────────────────────────
const {
  FaRocket, FaChartLine, FaLightbulb, FaUsers, FaCog, FaShieldAlt,
  FaGlobe, FaStar, FaCheckCircle, FaArrowRight, FaDatabase, FaBrain,
  FaHandshake, FaTrophy, FaLeaf, FaBolt, FaHeart, FaLock, FaSearch,
  FaChartBar, FaIndustry, FaMobileAlt, FaCloud, FaCode, FaMoneyBillWave,
  FaGraduationCap, FaAtom, FaRecycle, FaComments
} = require("react-icons/fa");

const { MdOutlineInsights, MdAnalytics, MdDashboard } = require("react-icons/md");

// ─── Color Palettes (premium 2025 designs) ───────────────────────────────────
const THEMES = {
  Blue: {
    name: "Blue",
    primary: "1A376C",
    secondary: "4A90D9",
    accent: "00C9FF",
    dark: "0D1B3E",
    light: "EBF4FF",
    text: "FFFFFF",
    textDark: "1A376C",
    textMid: "4A6FA5",
    textLight: "A8C8F0",
    bg: "F0F4FF",
    card: "FFFFFF",
    gradient1: "1A376C",
    gradient2: "2E6DB4",
    chartColors: ["1A376C", "4A90D9", "00C9FF", "0D1B3E", "A8D8FF"],
  },
  Black: {
    name: "Black",
    primary: "1C1C1C",
    secondary: "E0A800",
    accent: "FFD700",
    dark: "0A0A0A",
    light: "F5F5F5",
    text: "FFFFFF",
    textDark: "1C1C1C",
    textMid: "555555",
    textLight: "AAAAAA",
    bg: "F5F5F5",
    card: "FFFFFF",
    gradient1: "1C1C1C",
    gradient2: "333333",
    chartColors: ["1C1C1C", "E0A800", "FFD700", "555555", "AAAAAA"],
  },
  White: {
    name: "White",
    primary: "2E86AB",
    secondary: "A23B72",
    accent: "F18F01",
    dark: "1A5276",
    light: "FAFAFA",
    text: "FFFFFF",
    textDark: "1C1C1C",
    textMid: "555555",
    textLight: "888888",
    bg: "FFFFFF",
    card: "F8FAFC",
    gradient1: "2E86AB",
    gradient2: "1A5276",
    chartColors: ["2E86AB", "A23B72", "F18F01", "1A5276", "5DADE2"],
  },
  Green: {
    name: "Green",
    primary: "10472F",
    secondary: "2DB86A",
    accent: "8FE03E",
    dark: "072419",
    light: "F0FDF4",
    text: "FFFFFF",
    textDark: "10472F",
    textMid: "2D7D52",
    textLight: "6FCF97",
    bg: "F0FDF4",
    card: "FFFFFF",
    gradient1: "10472F",
    gradient2: "1A6640",
    chartColors: ["10472F", "2DB86A", "8FE03E", "1A6640", "A8F0B0"],
  },
  PremiumDark: {
    name: "PremiumDark",
    primary: "0D0D1A",
    secondary: "9B59B6",
    accent: "E74C3C",
    dark: "050510",
    light: "1A1A2E",
    text: "FFFFFF",
    textDark: "EEEEFF",
    textMid: "CCAAFF",
    textLight: "9980CC",
    bg: "12122A",
    card: "1A1A35",
    gradient1: "0D0D1A",
    gradient2: "1A0D2E",
    chartColors: ["9B59B6", "E74C3C", "3498DB", "1ABC9C", "F39C12"],
  },
};

// ─── Icon Helper ──────────────────────────────────────────────────────────────
async function iconToBase64(IconComponent, color = "#FFFFFF", size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
  const pngBuffer = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + pngBuffer.toString("base64");
}

// ─── Fetch image from URL ─────────────────────────────────────────────────────
function fetchImageBuffer(url) {
  return new Promise((resolve) => {
    const client = url.startsWith("https") ? https : http;
    const req = client.get(url, { timeout: 8000 }, (res) => {
      if (res.statusCode === 301 || res.statusCode === 302) {
        fetchImageBuffer(res.headers.location).then(resolve);
        return;
      }
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () => resolve(Buffer.concat(chunks)));
    });
    req.on("error", () => resolve(null));
    req.on("timeout", () => { req.destroy(); resolve(null); });
  });
}

// Unsplash curated photo IDs per topic category
const UNSPLASH_TOPICS = {
  technology: [
    "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&q=80",
    "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=800&q=80",
    "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=800&q=80",
  ],
  business: [
    "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=800&q=80",
    "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800&q=80",
    "https://images.unsplash.com/photo-1520607162513-77705c0f0d4a?w=800&q=80",
  ],
  nature: [
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800&q=80",
    "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80",
    "https://images.unsplash.com/photo-1518173946687-a4c8892bbd9f?w=800&q=80",
  ],
  education: [
    "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=800&q=80",
    "https://images.unsplash.com/photo-1509062522246-3755977927d7?w=800&q=80",
    "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=800&q=80",
  ],
  abstract: [
    "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=800&q=80",
    "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=800&q=80",
    "https://images.unsplash.com/photo-1516192518150-0d8fee5425e3?w=800&q=80",
  ],
  ai: [
    "https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=800&q=80",
    "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=800&q=80",
    "https://images.unsplash.com/photo-1684369175833-4b445ad6bfb5?w=800&q=80",
  ],
  people: [
    "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800&q=80",
    "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=800&q=80",
    "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=800&q=80",
  ],
  finance: [
    "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&q=80",
    "https://images.unsplash.com/photo-1559526324-593bc073d938?w=800&q=80",
    "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&q=80",
  ],
};

function getImageUrls(topic = "") {
  const t = topic.toLowerCase();
  if (t.includes("ai") || t.includes("sun'iy") || t.includes("intellekt")) return UNSPLASH_TOPICS.ai;
  if (t.includes("tech") || t.includes("texnolog") || t.includes("digital")) return UNSPLASH_TOPICS.technology;
  if (t.includes("biznes") || t.includes("business") || t.includes("marketing")) return UNSPLASH_TOPICS.business;
  if (t.includes("tabiat") || t.includes("nature") || t.includes("iqlim") || t.includes("ekolog")) return UNSPLASH_TOPICS.nature;
  if (t.includes("ta'lim") || t.includes("educ") || t.includes("maktab") || t.includes("univer")) return UNSPLASH_TOPICS.education;
  if (t.includes("moliya") || t.includes("finan") || t.includes("iqtisod")) return UNSPLASH_TOPICS.finance;
  if (t.includes("jamiyat") || t.includes("ijtimoiy") || t.includes("people")) return UNSPLASH_TOPICS.people;
  return UNSPLASH_TOPICS.abstract;
}

// ─── Slide Icon Sets ──────────────────────────────────────────────────────────
const SLIDE_ICONS = [
  FaRocket, FaChartLine, FaLightbulb, FaUsers, FaCog, FaShieldAlt,
  FaGlobe, FaStar, FaDatabase, FaBrain, FaHandshake, FaTrophy,
  FaLeaf, FaBolt, FaHeart, FaLock, FaSearch, FaChartBar,
  FaIndustry, FaMobileAlt, FaCloud, FaCode, FaMoneyBillWave,
  FaGraduationCap, FaAtom, FaRecycle, FaComments
];

// ─── Main Generator ───────────────────────────────────────────────────────────
async function generatePptx(data, colorScheme = "Blue", outputPath = "output.pptx") {
  const theme = THEMES[colorScheme] || THEMES["Blue"];
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.3" x 7.5"
  pres.title = data.title || "Taqdimot";
  pres.author = "AI Taqdimot Ustasi";

  const slides = data.slides || [];
  const totalSlides = slides.length;
  const topic = data.title || "";

  // Pre-fetch images
  const imageUrls = getImageUrls(topic);
  const imageBuffers = [];
  for (let i = 0; i < Math.min(3, imageUrls.length); i++) {
    const buf = await fetchImageBuffer(imageUrls[i]);
    if (buf) {
      const b64 = buf.toString("base64");
      imageBuffers.push("image/jpeg;base64," + b64);
    } else {
      imageBuffers.push(null);
    }
  }

  // Pre-render icons
  const iconCache = {};
  const iconColors = ["FFFFFF", "FFFFFF", theme.accent, theme.secondary];
  async function getIcon(IconComp, colorHex = "FFFFFF") {
    const key = `${IconComp.name}_${colorHex}`;
    if (!iconCache[key]) {
      iconCache[key] = await iconToBase64(IconComp, "#" + colorHex, 256);
    }
    return iconCache[key];
  }

  // Pre-render main icons
  const mainIcons = [];
  for (let i = 0; i < Math.min(totalSlides + 5, SLIDE_ICONS.length); i++) {
    mainIcons.push(await getIcon(SLIDE_ICONS[i], "FFFFFF"));
  }
  const accentIcons = [];
  for (let i = 0; i < Math.min(totalSlides + 5, SLIDE_ICONS.length); i++) {
    accentIcons.push(await getIcon(SLIDE_ICONS[i], theme.accent));
  }
  const primaryColorIcons = [];
  for (let i = 0; i < Math.min(totalSlides + 5, SLIDE_ICONS.length); i++) {
    primaryColorIcons.push(await getIcon(SLIDE_ICONS[i], theme.secondary));
  }

  const checkIcon = await getIcon(FaCheckCircle, theme.secondary);
  const checkIconWhite = await getIcon(FaCheckCircle, "FFFFFF");
  const arrowIcon = await getIcon(FaArrowRight, theme.accent);
  const starIcon = await getIcon(FaStar, theme.accent);
  const starWhite = await getIcon(FaStar, "FFFFFF");

  // W=13.33, H=7.5
  const W = 13.33, H = 7.5;

  // ─── LAYOUT FUNCTIONS ─────────────────────────────────────────────────────

  // Layout 1: Hero Title Slide (dark full-bleed + large text)
  function layoutHeroTitle(slide, sd, idx) {
    slide.background = { color: theme.gradient1 };

    // Large decorative circle top-right
    slide.addShape(pres.ShapeType.ellipse, {
      x: W - 3.5, y: -1.5, w: 5, h: 5,
      fill: { color: theme.secondary, transparency: 80 }, line: { color: theme.secondary, transparency: 80 }
    });
    slide.addShape(pres.ShapeType.ellipse, {
      x: W - 2.5, y: -0.5, w: 3.5, h: 3.5,
      fill: { color: theme.accent, transparency: 85 }, line: { color: theme.accent, transparency: 85 }
    });

    // Left side accent line
    slide.addShape(pres.ShapeType.rect, {
      x: 0.8, y: 1.8, w: 0.08, h: 2.5,
      fill: { color: theme.accent }, line: { color: theme.accent }
    });

    // Main image right side (if available)
    if (imageBuffers[0]) {
      slide.addImage({ data: imageBuffers[0], x: W - 5.5, y: 1.2, w: 4.8, h: 5.5,
        transparency: 20, sizing: { type: "cover", w: 4.8, h: 5.5 } });
      // gradient overlay over image
      slide.addShape(pres.ShapeType.rect, {
        x: W - 5.5, y: 1.2, w: 4.8, h: 5.5,
        fill: { color: theme.gradient1, transparency: 30 }, line: { color: "transparent", transparency: 100 }
      });
    }

    // Title
    slide.addText(sd.title || "Taqdimot", {
      x: 1.1, y: 1.8, w: 7.5, h: 1.8,
      fontSize: 52, bold: true, color: theme.text,
      fontFace: "Calibri", margin: 0
    });

    // Subtitle / content
    const subtitle = sd.content || data.title || "";
    if (subtitle) {
      slide.addText(subtitle, {
        x: 1.1, y: 3.8, w: 6.5, h: 1.2,
        fontSize: 18, color: theme.textLight,
        fontFace: "Calibri Light", margin: 0
      });
    }

    // Slide counter pill
    slide.addShape(pres.ShapeType.roundRect, {
      x: 1.1, y: H - 1.1, w: 1.4, h: 0.45,
      fill: { color: theme.accent, transparency: 20 }, line: { color: theme.accent, transparency: 20 },
      rectRadius: 0.15
    });
    slide.addText(`1 / ${totalSlides}`, {
      x: 1.1, y: H - 1.1, w: 1.4, h: 0.45,
      fontSize: 11, color: theme.text, align: "center", bold: true, margin: 0
    });

    // Icon top left
    if (mainIcons[0]) {
      slide.addImage({ data: mainIcons[0], x: 1.0, y: 1.0, w: 0.5, h: 0.5 });
    }
  }

  // Layout 2: Split layout (image left, content right)
  function layoutSplitImageLeft(slide, sd, idx) {
    slide.background = { color: theme.bg };

    // Left image panel
    if (imageBuffers[idx % imageBuffers.length] || imageBuffers[0]) {
      const imgData = imageBuffers[idx % imageBuffers.length] || imageBuffers[0];
      slide.addShape(pres.ShapeType.rect, {
        x: 0, y: 0, w: 5.2, h: H,
        fill: { color: theme.primary }, line: { color: theme.primary }
      });
      if (imgData) {
        slide.addImage({ data: imgData, x: 0, y: 0, w: 5.2, h: H,
          transparency: 25, sizing: { type: "cover", w: 5.2, h: H } });
      }
      // Gradient overlay on image
      slide.addShape(pres.ShapeType.rect, {
        x: 0, y: 0, w: 5.2, h: H,
        fill: { color: theme.primary, transparency: 50 }, line: { color: "transparent", transparency: 100 }
      });
    }

    // Slide number on image
    slide.addText(`${idx + 1}`, {
      x: 0, y: H - 1.0, w: 5.2, h: 0.8,
      fontSize: 60, bold: true, color: theme.text,
      align: "center", fontFace: "Calibri", margin: 0,
      transparency: 30
    });

    // Right content area
    const kp = sd.key_points || [];
    const rightX = 5.5;

    // Top accent bar
    slide.addShape(pres.ShapeType.rect, {
      x: rightX, y: 0, w: W - rightX, h: 0.08,
      fill: { color: theme.secondary }, line: { color: theme.secondary }
    });

    // Icon + Title row
    const iconIdx = idx % mainIcons.length;
    if (accentIcons[iconIdx]) {
      slide.addShape(pres.ShapeType.ellipse, {
        x: rightX, y: 0.4, w: 0.7, h: 0.7,
        fill: { color: theme.primary }, line: { color: theme.primary }
      });
      slide.addImage({ data: accentIcons[iconIdx], x: rightX + 0.12, y: 0.52, w: 0.46, h: 0.46 });
    }

    slide.addText(sd.title || "", {
      x: rightX + 0.85, y: 0.4, w: W - rightX - 1.1, h: 0.85,
      fontSize: 26, bold: true, color: theme.textDark,
      fontFace: "Calibri", margin: 0
    });

    // Content text
    slide.addText(sd.content || "", {
      x: rightX, y: 1.5, w: W - rightX - 0.5, h: 2.0,
      fontSize: 14, color: theme.textMid,
      fontFace: "Calibri Light", margin: 0
    });

    // Key points as cards
    if (kp.length > 0) {
      const kpY = 3.6;
      slide.addText("Kalit fikrlar", {
        x: rightX, y: kpY - 0.35, w: 3.5, h: 0.35,
        fontSize: 11, bold: true, color: theme.secondary,
        fontFace: "Calibri", margin: 0, charSpacing: 2
      });
      kp.slice(0, 4).forEach((kpText, i) => {
        const row = Math.floor(i / 2), col = i % 2;
        const cx = rightX + col * 3.7;
        const cy = kpY + row * 1.1;
        slide.addShape(pres.ShapeType.roundRect, {
          x: cx, y: cy, w: 3.5, h: 0.9,
          fill: { color: theme.card },
          shadow: { type: "outer", blur: 4, offset: 1, angle: 135, color: "000000", opacity: 0.08 },
          line: { color: theme.secondary, width: 1, transparency: 70 },
          rectRadius: 0.08
        });
        if (checkIcon) {
          slide.addImage({ data: checkIcon, x: cx + 0.12, y: cy + 0.22, w: 0.3, h: 0.3 });
        }
        slide.addText(kpText, {
          x: cx + 0.52, y: cy + 0.15, w: 2.85, h: 0.6,
          fontSize: 11, color: theme.textDark, margin: 0,
          fontFace: "Calibri"
        });
      });
    }

    // Slide counter
    slide.addText(`${idx + 1} / ${totalSlides}`, {
      x: W - 1.5, y: H - 0.45, w: 1.3, h: 0.35,
      fontSize: 10, color: theme.textLight, align: "right", margin: 0
    });
  }

  // Layout 3: Cards grid (2x2 or 3x1 key points)
  function layoutCardsGrid(slide, sd, idx) {
    slide.background = { color: theme.bg };

    // Header band
    slide.addShape(pres.ShapeType.rect, {
      x: 0, y: 0, w: W, h: 1.3,
      fill: { color: theme.primary }, line: { color: theme.primary }
    });

    // Icon in header
    const iconIdx = idx % mainIcons.length;
    if (mainIcons[iconIdx]) {
      slide.addImage({ data: mainIcons[iconIdx], x: 0.4, y: 0.3, w: 0.65, h: 0.65 });
    }
    slide.addText(sd.title || "", {
      x: 1.3, y: 0.2, w: W - 3.0, h: 0.9,
      fontSize: 28, bold: true, color: theme.text,
      fontFace: "Calibri", margin: 0
    });
    slide.addText(`${idx + 1} / ${totalSlides}`, {
      x: W - 1.5, y: 0.4, w: 1.3, h: 0.5,
      fontSize: 11, color: theme.textLight, align: "right", margin: 0
    });

    // Content paragraph
    slide.addText(sd.content || "", {
      x: 0.5, y: 1.5, w: W - 1.0, h: 1.2,
      fontSize: 14, color: theme.textMid,
      fontFace: "Calibri Light", margin: 0
    });

    // Key points as large feature cards (up to 4)
    const kp = sd.key_points || [];
    if (kp.length > 0) {
      const displayKp = kp.slice(0, 4);
      const cols = Math.min(displayKp.length, 2);
      const rows = Math.ceil(displayKp.length / cols);
      const cardW = (W - 0.8 - (cols - 1) * 0.3) / cols;
      const cardH = rows === 1 ? 1.8 : 1.3;

      displayKp.forEach((kpText, i) => {
        const col = i % cols, row = Math.floor(i / cols);
        const cx = 0.4 + col * (cardW + 0.3);
        const cy = 2.9 + row * (cardH + 0.25);

        // Card background
        slide.addShape(pres.ShapeType.roundRect, {
          x: cx, y: cy, w: cardW, h: cardH,
          fill: { color: theme.card },
          shadow: { type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.1 },
          line: { color: theme.card },
          rectRadius: 0.12
        });
        // Accent left strip
        slide.addShape(pres.ShapeType.rect, {
          x: cx, y: cy, w: 0.08, h: cardH,
          fill: { color: theme.secondary }, line: { color: theme.secondary }
        });

        const icIdx = (i + idx * 4) % SLIDE_ICONS.length;
        const icPrim = primaryColorIcons[icIdx] || accentIcons[0];
        if (icPrim) {
          slide.addImage({ data: icPrim, x: cx + 0.18, y: cy + 0.18, w: 0.5, h: 0.5 });
        }
        slide.addText(kpText, {
          x: cx + 0.82, y: cy + 0.12, w: cardW - 1.0, h: cardH - 0.24,
          fontSize: 13, color: theme.textDark, margin: 0,
          fontFace: "Calibri"
        });
      });
    }

    // Image thumbnail if available
    const imgIdx = idx % imageBuffers.length;
    if (imageBuffers[imgIdx] && kp.length < 3) {
      slide.addImage({
        data: imageBuffers[imgIdx],
        x: W - 4.0, y: 2.8, w: 3.5, h: 2.5,
        sizing: { type: "cover", w: 3.5, h: 2.5 }
      });
    }
  }

  // Layout 4: Full-bleed image + text overlay
  function layoutImageOverlay(slide, sd, idx) {
    slide.background = { color: theme.primary };

    // Try any available image
    const validImages = imageBuffers.filter(Boolean);
    const imgData = validImages.length > 0 ? validImages[idx % validImages.length] : null;
    if (imgData) {
      slide.addImage({ data: imgData, x: 0, y: 0, w: W, h: H,
        sizing: { type: "cover", w: W, h: H } });
    }

    // Dark overlay for readability
    slide.addShape(pres.ShapeType.rect, {
      x: 0, y: 0, w: W, h: H,
      fill: { color: theme.primary, transparency: imgData ? 45 : 0 },
      line: { color: theme.primary, transparency: 100 }
    });

    // Bottom overlay panel
    slide.addShape(pres.ShapeType.rect, {
      x: 0, y: H - 3.5, w: W, h: 3.5,
      fill: { color: theme.dark, transparency: imgData ? 20 : 0 },
      line: { color: theme.dark, transparency: 100 }
    });

    // Accent line
    slide.addShape(pres.ShapeType.rect, {
      x: 0.8, y: H - 3.2, w: 1.5, h: 0.07,
      fill: { color: theme.accent }, line: { color: theme.accent }
    });

    slide.addText(sd.title || "", {
      x: 0.8, y: H - 2.95, w: W - 1.6, h: 1.0,
      fontSize: 36, bold: true, color: theme.text,
      fontFace: "Calibri", margin: 0
    });
    slide.addText(sd.content || "", {
      x: 0.8, y: H - 1.85, w: W - 1.6, h: 1.2,
      fontSize: 14, color: theme.textLight,
      fontFace: "Calibri Light", margin: 0
    });

    // Slide counter
    slide.addText(`${idx + 1} / ${totalSlides}`, {
      x: W - 1.5, y: 0.2, w: 1.3, h: 0.4,
      fontSize: 11, color: theme.text, align: "right", margin: 0
    });
  }

  // Layout 5: Stats / Big Numbers layout
  function layoutStats(slide, sd, idx) {
    slide.background = { color: theme.bg };

    // Left content column
    slide.addShape(pres.ShapeType.rect, {
      x: 0, y: 0, w: 4.8, h: H,
      fill: { color: theme.primary }, line: { color: theme.primary }
    });

    const iconIdx = idx % mainIcons.length;
    if (mainIcons[iconIdx]) {
      slide.addImage({ data: mainIcons[iconIdx], x: 0.5, y: 0.5, w: 1.0, h: 1.0 });
    }

    slide.addText(sd.title || "", {
      x: 0.4, y: 1.8, w: 4.0, h: 1.6,
      fontSize: 28, bold: true, color: theme.text,
      fontFace: "Calibri", margin: 0
    });
    slide.addText(sd.content || "", {
      x: 0.4, y: 3.6, w: 4.0, h: 2.2,
      fontSize: 13, color: theme.textLight,
      fontFace: "Calibri Light", margin: 0
    });

    // Image on left at bottom
    if (imageBuffers[idx % imageBuffers.length]) {
      slide.addImage({
        data: imageBuffers[idx % imageBuffers.length],
        x: 0, y: H - 1.5, w: 4.8, h: 1.5,
        transparency: 60, sizing: { type: "cover", w: 4.8, h: 1.5 }
      });
    }

    // Right stats cards
    const kp = (sd.key_points || []).slice(0, 4);
    const statsY = [0.3, 1.85, 3.4, 5.0];
    const statIcons = [FaStar, FaTrophy, FaBolt, FaCheckCircle];

    kp.forEach((text, i) => {
      const cy = statsY[i] || (0.3 + i * 1.7);
      slide.addShape(pres.ShapeType.roundRect, {
        x: 5.2, y: cy, w: W - 5.6, h: 1.45,
        fill: { color: theme.card },
        shadow: { type: "outer", blur: 5, offset: 2, angle: 135, color: "000000", opacity: 0.09 },
        line: { color: theme.card },
        rectRadius: 0.1
      });
      // Number badge
      slide.addShape(pres.ShapeType.ellipse, {
        x: 5.3, y: cy + 0.32, w: 0.8, h: 0.8,
        fill: { color: theme.secondary }, line: { color: theme.secondary }
      });
      slide.addText(`${i + 1}`, {
        x: 5.3, y: cy + 0.32, w: 0.8, h: 0.8,
        fontSize: 18, bold: true, color: "FFFFFF",
        align: "center", valign: "middle", margin: 0
      });
      slide.addText(text, {
        x: 6.3, y: cy + 0.2, w: W - 6.9, h: 1.05,
        fontSize: 13, color: theme.textDark, margin: 0,
        fontFace: "Calibri"
      });
    });

    slide.addText(`${idx + 1} / ${totalSlides}`, {
      x: W - 1.5, y: H - 0.45, w: 1.3, h: 0.35,
      fontSize: 10, color: theme.textLight, align: "right", margin: 0
    });
  }

  // Layout 6: Timeline / Process flow
  function layoutTimeline(slide, sd, idx) {
    slide.background = { color: theme.bg };

    // Top header
    slide.addShape(pres.ShapeType.rect, {
      x: 0, y: 0, w: W, h: 1.2,
      fill: { color: theme.primary }, line: { color: theme.primary }
    });
    const iconIdx = idx % mainIcons.length;
    if (mainIcons[iconIdx]) {
      slide.addImage({ data: mainIcons[iconIdx], x: 0.35, y: 0.25, w: 0.7, h: 0.7 });
    }
    slide.addText(sd.title || "", {
      x: 1.3, y: 0.2, w: W - 3.5, h: 0.8,
      fontSize: 28, bold: true, color: theme.text,
      fontFace: "Calibri", margin: 0
    });
    slide.addText(`${idx + 1} / ${totalSlides}`, {
      x: W - 1.5, y: 0.35, w: 1.3, h: 0.5,
      fontSize: 11, color: theme.textLight, align: "right", margin: 0
    });

    // Content
    slide.addText(sd.content || "", {
      x: 0.5, y: 1.4, w: W - 1.0, h: 1.0,
      fontSize: 14, color: theme.textMid,
      fontFace: "Calibri Light", margin: 0
    });

    // Timeline steps
    const kp = (sd.key_points || []).slice(0, 5);
    if (kp.length > 0) {
      const startX = 0.5;
      const stepW = (W - 1.0) / kp.length;
      const lineY = 3.8;

      // Horizontal line
      slide.addShape(pres.ShapeType.rect, {
        x: startX + 0.35, y: lineY + 0.3, w: W - 1.0 - 0.7, h: 0.06,
        fill: { color: theme.secondary }, line: { color: theme.secondary }
      });

      kp.forEach((step, i) => {
        const cx = startX + i * stepW;

        // Step circle
        slide.addShape(pres.ShapeType.ellipse, {
          x: cx + stepW / 2 - 0.35, y: lineY + 0.03, w: 0.7, h: 0.7,
          fill: { color: i === 0 ? theme.accent : theme.primary },
          line: { color: theme.secondary, width: 2 }
        });
        slide.addText(`${i + 1}`, {
          x: cx + stepW / 2 - 0.35, y: lineY + 0.03, w: 0.7, h: 0.7,
          fontSize: 16, bold: true, color: "FFFFFF",
          align: "center", valign: "middle", margin: 0
        });

        // Step text below
        slide.addText(step, {
          x: cx + 0.1, y: lineY + 0.9, w: stepW - 0.2, h: 1.8,
          fontSize: 12, color: theme.textDark, align: "center",
          fontFace: "Calibri", margin: 0
        });
      });
    }

    // Image strip at bottom right
    if (imageBuffers[idx % imageBuffers.length] && (sd.key_points || []).length < 4) {
      slide.addImage({
        data: imageBuffers[idx % imageBuffers.length],
        x: W - 4.2, y: 1.4, w: 3.7, h: 2.5,
        sizing: { type: "cover", w: 3.7, h: 2.5 }
      });
    }
  }

  // Layout 7: Minimal centered (for summary/conclusion slides)
  function layoutMinimalCentered(slide, sd, idx) {
    slide.background = { color: theme.primary };

    // Background image with high transparency
    if (imageBuffers[0]) {
      slide.addImage({ data: imageBuffers[0], x: 0, y: 0, w: W, h: H,
        sizing: { type: "cover", w: W, h: H }, transparency: 70 });
    }

    // Large decorative circle
    slide.addShape(pres.ShapeType.ellipse, {
      x: W / 2 - 2.5, y: H / 2 - 2.5, w: 5, h: 5,
      fill: { color: theme.secondary, transparency: 85 },
      line: { color: theme.accent, transparency: 60, width: 2 }
    });

    const iconIdx = idx % mainIcons.length;
    if (mainIcons[iconIdx]) {
      slide.addImage({ data: mainIcons[iconIdx], x: W / 2 - 0.4, y: 1.5, w: 0.8, h: 0.8 });
    }

    slide.addText(sd.title || "", {
      x: 1.5, y: 2.4, w: W - 3, h: 1.4,
      fontSize: 42, bold: true, color: theme.text,
      fontFace: "Calibri", align: "center", margin: 0
    });

    slide.addText(sd.content || "", {
      x: 2.0, y: 4.1, w: W - 4, h: 1.5,
      fontSize: 16, color: theme.textLight,
      fontFace: "Calibri Light", align: "center", margin: 0
    });

    slide.addText(`${idx + 1} / ${totalSlides}`, {
      x: W - 1.5, y: H - 0.5, w: 1.3, h: 0.4,
      fontSize: 11, color: theme.textLight, align: "right", margin: 0
    });
  }

  // Layout 8: Two columns comparison
  function layoutTwoColumns(slide, sd, idx) {
    slide.background = { color: theme.bg };

    // Header
    slide.addShape(pres.ShapeType.rect, {
      x: 0, y: 0, w: W, h: 1.1,
      fill: { color: theme.primary }, line: { color: theme.primary }
    });
    const iconIdx = idx % mainIcons.length;
    if (mainIcons[iconIdx]) {
      slide.addImage({ data: mainIcons[iconIdx], x: 0.35, y: 0.22, w: 0.65, h: 0.65 });
    }
    slide.addText(sd.title || "", {
      x: 1.2, y: 0.17, w: W - 2.8, h: 0.76,
      fontSize: 26, bold: true, color: theme.text,
      fontFace: "Calibri", margin: 0
    });
    slide.addText(`${idx + 1} / ${totalSlides}`, {
      x: W - 1.5, y: 0.3, w: 1.3, h: 0.5,
      fontSize: 11, color: theme.textLight, align: "right", margin: 0
    });

    // Content
    slide.addText(sd.content || "", {
      x: 0.5, y: 1.25, w: W - 1.0, h: 0.95,
      fontSize: 13, color: theme.textMid,
      fontFace: "Calibri Light", margin: 0
    });

    // Two column cards
    const kp = (sd.key_points || []).slice(0, 6);
    const half = Math.ceil(kp.length / 2);
    [[0, kp.slice(0, half)], [1, kp.slice(half)]].forEach(([col, items]) => {
      const cx = col === 0 ? 0.4 : W / 2 + 0.2;
      const cw = W / 2 - 0.6;

      // Column header
      slide.addShape(pres.ShapeType.roundRect, {
        x: cx, y: 2.3, w: cw, h: 0.5,
        fill: { color: col === 0 ? theme.primary : theme.secondary },
        line: { color: col === 0 ? theme.primary : theme.secondary },
        rectRadius: 0.06
      });
      slide.addText(col === 0 ? "✦ Asosiy fikrlar" : "✦ Qo'shimcha", {
        x: cx + 0.15, y: 2.3, w: cw - 0.3, h: 0.5,
        fontSize: 12, bold: true, color: "FFFFFF", margin: 0
      });

      items.forEach((item, i) => {
        const ry = 2.95 + i * 0.88;
        slide.addShape(pres.ShapeType.roundRect, {
          x: cx, y: ry, w: cw, h: 0.75,
          fill: { color: theme.card },
          shadow: { type: "outer", blur: 3, offset: 1, angle: 135, color: "000000", opacity: 0.07 },
          line: { color: col === 0 ? theme.primary : theme.secondary, transparency: 75 },
          rectRadius: 0.07
        });
        if (checkIcon) {
          slide.addImage({ data: checkIcon, x: cx + 0.12, y: ry + 0.2, w: 0.3, h: 0.3 });
        }
        slide.addText(item, {
          x: cx + 0.55, y: ry + 0.1, w: cw - 0.7, h: 0.55,
          fontSize: 12, color: theme.textDark, margin: 0
        });
      });
    });
  }

  // Layout 9: Feature spotlight (big icon + content)
  function layoutFeatureSpotlight(slide, sd, idx) {
    slide.background = { color: theme.bg };

    // Top right decorative shape
    slide.addShape(pres.ShapeType.ellipse, {
      x: W - 4.0, y: -1.5, w: 5.5, h: 5.5,
      fill: { color: theme.primary, transparency: 90 },
      line: { color: theme.secondary, transparency: 75, width: 1 }
    });

    // Big icon circle
    const iconIdx = idx % mainIcons.length;
    slide.addShape(pres.ShapeType.ellipse, {
      x: 0.6, y: 1.2, w: 2.2, h: 2.2,
      fill: { color: theme.primary }, line: { color: theme.secondary, width: 2 }
    });
    if (mainIcons[iconIdx]) {
      slide.addImage({ data: mainIcons[iconIdx], x: 0.98, y: 1.58, w: 1.44, h: 1.44 });
    }

    // Image in top right
    if (imageBuffers[idx % imageBuffers.length]) {
      slide.addImage({
        data: imageBuffers[idx % imageBuffers.length],
        x: W - 4.8, y: 0.3, w: 4.5, h: 3.2,
        sizing: { type: "cover", w: 4.5, h: 3.2 }
      });
    }

    // Title
    slide.addText(sd.title || "", {
      x: 3.2, y: 1.2, w: W - 8.2, h: 1.0,
      fontSize: 30, bold: true, color: theme.textDark,
      fontFace: "Calibri", margin: 0
    });
    // Content
    slide.addText(sd.content || "", {
      x: 3.2, y: 2.4, w: W - 8.2, h: 1.2,
      fontSize: 13, color: theme.textMid,
      fontFace: "Calibri Light", margin: 0
    });

    // Bottom full-width key points strip
    const kp = (sd.key_points || []).slice(0, 4);
    if (kp.length > 0) {
      slide.addShape(pres.ShapeType.rect, {
        x: 0, y: H - 2.2, w: W, h: 2.2,
        fill: { color: theme.light }, line: { color: theme.light }
      });
      slide.addShape(pres.ShapeType.rect, {
        x: 0, y: H - 2.2, w: W, h: 0.06,
        fill: { color: theme.secondary }, line: { color: theme.secondary }
      });

      kp.forEach((item, i) => {
        const cx = 0.5 + i * ((W - 0.8) / 4);
        const cw = (W - 0.8) / 4 - 0.2;
        if (accentIcons[i % accentIcons.length]) {
          slide.addImage({
            data: accentIcons[i % accentIcons.length],
            x: cx, y: H - 2.0, w: 0.45, h: 0.45
          });
        }
        slide.addText(item, {
          x: cx + 0.55, y: H - 2.0, w: cw - 0.6, h: 1.8,
          fontSize: 11, color: theme.textDark, margin: 0
        });
      });
    }

    slide.addText(`${idx + 1} / ${totalSlides}`, {
      x: W - 1.5, y: H - 0.45, w: 1.3, h: 0.35,
      fontSize: 10, color: theme.textLight, align: "right", margin: 0
    });
  }

  // Layout 10: Closing / Thank You slide
  function layoutClosing(slide, sd, idx) {
    slide.background = { color: theme.gradient1 };

    // Background image low opacity
    if (imageBuffers[1] || imageBuffers[0]) {
      const img = imageBuffers[1] || imageBuffers[0];
      slide.addImage({ data: img, x: 0, y: 0, w: W, h: H,
        sizing: { type: "cover", w: W, h: H }, transparency: 75 });
    }

    // Decorative shapes
    slide.addShape(pres.ShapeType.ellipse, {
      x: -1, y: -1, w: 4, h: 4,
      fill: { color: theme.accent, transparency: 85 }, line: { color: theme.accent, transparency: 80 }
    });
    slide.addShape(pres.ShapeType.ellipse, {
      x: W - 3.5, y: H - 3.5, w: 5, h: 5,
      fill: { color: theme.secondary, transparency: 80 }, line: { color: theme.secondary, transparency: 75 }
    });

    // Center content
    if (starWhite) {
      slide.addImage({ data: starWhite, x: W / 2 - 0.6, y: 0.9, w: 1.2, h: 1.2 });
    }

    slide.addText(sd.title || "Xulosa", {
      x: 1.5, y: 2.3, w: W - 3, h: 1.3,
      fontSize: 48, bold: true, color: theme.text,
      fontFace: "Calibri", align: "center", margin: 0
    });

    const subtitle = sd.content || "";
    if (subtitle) {
      slide.addText(subtitle, {
        x: 2.0, y: 3.8, w: W - 4, h: 1.2,
        fontSize: 16, color: theme.textLight,
        fontFace: "Calibri Light", align: "center", margin: 0
      });
    }

    // Key points as pill tags
    const kp = (sd.key_points || []).slice(0, 4);
    if (kp.length > 0) {
      const totalWidth = kp.length * 2.8 + (kp.length - 1) * 0.3;
      const startX = (W - totalWidth) / 2;
      kp.forEach((item, i) => {
        const cx = startX + i * 3.1;
        slide.addShape(pres.ShapeType.roundRect, {
          x: cx, y: 5.3, w: 2.8, h: 0.65,
          fill: { color: theme.accent, transparency: 25 },
          line: { color: theme.accent, transparency: 50 },
          rectRadius: 0.2
        });
        slide.addText(item, {
          x: cx, y: 5.3, w: 2.8, h: 0.65,
          fontSize: 11, bold: true, color: "FFFFFF",
          align: "center", margin: 0
        });
      });
    }

    // Branding
    slide.addText("AI Taqdimot Ustasi", {
      x: 0, y: H - 0.5, w: W, h: 0.4,
      fontSize: 10, color: theme.textLight,
      align: "center", margin: 0
    });
  }

  // ─── Choose layout per slide ───────────────────────────────────────────────
  const LAYOUTS = [
    layoutHeroTitle,        // 0 - title slide
    layoutSplitImageLeft,   // 1
    layoutCardsGrid,        // 2
    layoutImageOverlay,     // 3
    layoutStats,            // 4
    layoutTimeline,         // 5
    layoutMinimalCentered,  // 6
    layoutTwoColumns,       // 7
    layoutFeatureSpotlight, // 8
  ];

  // ─── Build slides ──────────────────────────────────────────────────────────
  for (let i = 0; i < totalSlides; i++) {
    const sd = slides[i];
    const slide = pres.addSlide();

    if (i === 0) {
      layoutHeroTitle(slide, sd, i);
    } else if (i === totalSlides - 1) {
      layoutClosing(slide, sd, i);
    } else {
      // Rotate through layouts 1-8
      const layoutIdx = ((i - 1) % (LAYOUTS.length - 1)) + 1;
      LAYOUTS[layoutIdx](slide, sd, i);
    }

    // Add speaker notes
    const notes = sd.speaker_notes || "";
    if (notes) {
      try {
        slide.addNotes(notes);
      } catch (e) {}
    }
  }

  await pres.writeFile({ fileName: outputPath });
  return outputPath;
}

// ─── CLI / test mode ──────────────────────────────────────────────────────────
if (require.main === module) {
  const dataPath = process.argv[2] || "test_data.json";
  const scheme = process.argv[3] || "Blue";
  const outPath = process.argv[4] || "/mnt/user-data/outputs/AI-Taqdimot-Ultra.pptx";

  const data = JSON.parse(fs.readFileSync(dataPath, "utf-8"));

  generatePptx(data, scheme, outPath)
    .then((p) => console.log("✅ Generated:", p))
    .catch((e) => { console.error("❌ Error:", e); process.exit(1); });
}

module.exports = { generatePptx };
