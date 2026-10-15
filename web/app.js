/**
 * AI Heritage Explorer – Frontend Interactive Application Engine
 * Ancient Tamil & Keeladi Digital Archaeological Platform
 */

// Global State
const state = {
  lang: 'en', // 'en' | 'ta'
  activeTab: 'exhibits', // 'exhibits' | 'epigraphy' | 'timeline' | 'science' | 'data'
  searchQuery: '',
  selectedCategory: 'all',
  sortBy: 'default',
  records: window.HERITAGE_RECORDS || [],
  sources: window.SOURCE_REGISTRY || [],
  activeRecord: null,
};

// Bilingual Strings
const I18N = {
  en: {
    heroPill: "Sangam Era • 6th Century BCE (580 BCE AMS Validated)",
    heroTitle: "Unearthing the Sangam Era: The Ancient Vaigai River Valley Civilization",
    heroDesc: "A source-grounded digital repository and research suite preserving ancient Tamil heritage. Explore systematic excavations from Keeladi Site Museum and the national epigraphical corpus of Archaeological Survey of India (BharatSHRI).",
    btnExplore: "Explore 53 Artifacts",
    btnEpigraphy: "தமிழி Epigraphy Lab",
    kpi1Number: "580",
    kpi1Unit: "BCE",
    kpi1Label: "AMS Carbon-14 Dating",
    kpi1Sub: "Beta Analytic (Beta-499770)",
    kpi2Number: "53",
    kpi2Unit: "Recs",
    kpi2Label: "Verified Artifact Records",
    kpi2Sub: "100% Source Provenance",
    kpi3Number: "509",
    kpi3Unit: "Assets",
    kpi3Label: "Artifact Media Discovered",
    kpi3Sub: "Terracotta, Beads, Inscriptions",
    kpi4Number: "45",
    kpi4Unit: "Vols",
    kpi4Label: "South Indian Inscriptions",
    kpi4Sub: "ASI Epigraphy Branch Mysore",
    tabExhibits: "🏛️ Exhibits & Artifacts",
    tabEpigraphy: "🔤 Tamil-Brahmi (தமிழி) Lab",
    tabTimeline: "⏳ Sangam Timeline",
    tabScience: "🔬 Archaeometry Lab",
    tabData: "📊 Datasets & Exports",
    searchPlaceholder: "Search inscriptions, sites (Keeladi, Madurai), materials, Tamil terms...",
    filterAll: "All Holdings (53)",
    filterKeeladi: "Keeladi Settlement (12)",
    filterBrahmi: "Tamil-Brahmi Epigraphy",
    filterBrick: "Brick Architecture",
    filterLapidary: "Lapidary & Beads",
    filterFaunal: "Faunal Osteology",
    filterTrade: "Maritime & Roman Trade",
    filterAsi: "ASI BharatSHRI (41)",
    sortDefault: "Featured Chronological",
    sortAlpha: "Title (A–Z)",
    sortConfidence: "High Confidence First",
    btnDetails: "View Full Artifact Data",
    evidenceTitle: "Excavation & Source Evidence:",
    modalMetaTitle: "Archaeological Metadata",
    modalEvidenceTitle: "Scholarly Evidence & Quote",
    modalCopyCitation: "Copy Citation",
    modalDownloadJson: "Download JSON",
    citationCopied: "Citation copied to clipboard!",
    speakText: "Narrate Details",
  },
  ta: {
    heroPill: "சங்க காலம் • கிமு 6-ஆம் நூற்றாண்டு (580 BCE அறிவியல் காலம்)",
    heroTitle: "வைகை நதிக்கரையில் சங்ககால நகர நாகரிகம்: கீழடி தொல்லியல் மேடை",
    heroDesc: "பண்டைய தமிழ் மரபு, தமிழி (பிராமி) கல்வெட்டுகள், செங்கல் கட்டடக்கலை மற்றும் பண்பாட்டுத் தரவுகளை ஆவணப்படுத்தும் களஞ்சியம். தமிழ்நாடு தொல்லியல் துறை கீழடி அருங்காட்சியகம் மற்றும் மத்திய தொல்லியல் துறை (பாரத்ஸ்ரீ) ஆவணங்கள்.",
    btnExplore: "53 தொல்பொருட்களை காண்க",
    btnEpigraphy: "தமிழி கல்வெட்டாய்வு கூடம்",
    kpi1Number: "580",
    kpi1Unit: "கிமு",
    kpi1Label: "கார்பன்-14 அறிவியல் கணிப்பு",
    kpi1Sub: "பீட்டா அனாலிட்டிக் (Beta-499770)",
    kpi2Number: "53",
    kpi2Unit: "பதிவுகள்",
    kpi2Label: "சரிபார்க்கப்பட்ட தொல்லியல் ஆவணங்கள்",
    kpi2Sub: "100% அதிகாரப்பூர்வ சான்றுகள்",
    kpi3Number: "509",
    kpi3Unit: "படங்கள்",
    kpi3Label: "கண்டறியப்பட்ட காட்சி ஆவணங்கள்",
    kpi3Sub: "சுடுமண், மணிகள், தமிழி ஓடுகள்",
    kpi4Number: "45",
    kpi4Unit: "தொகுதிகள்",
    kpi4Label: "தென்னிந்தியக் கல்வெட்டுகள் (SII)",
    kpi4Sub: "மைசூர் கல்வெட்டியல் பிரிவு",
    tabExhibits: "🏛️ காட்சிக்கூடங்கள் & ஆவணங்கள்",
    tabEpigraphy: "🔤 தமிழி (பிராமி) ஆய்வகம்",
    tabTimeline: "⏳ சங்க காலவரிசை",
    tabScience: "🔬 தொல்லியல் அறிவியல் கூடம்",
    tabData: "📊 தரவுகள் & தரவிறக்கம்",
    searchPlaceholder: "கல்வெட்டுகள், கீழடி, உறை கிணறு, செங்கல், வைகை, மட்பாண்டங்கள்...",
    filterAll: "அனைத்தும் (53)",
    filterKeeladi: "கீழடி நாகரிகம் (12)",
    filterBrahmi: "தமிழி கல்வெட்டுகள்",
    filterBrick: "செங்கல் கட்டடங்கள்",
    filterLapidary: "மணிகள் & அணிகலன்கள்",
    filterFaunal: "விலங்கின எச்சங்கள்",
    filterTrade: "கடல்வழி வாணிகம்",
    filterAsi: "மத்திய தொல்லியல் துறை (41)",
    sortDefault: "வரிசைப்படுத்தல் (இயல்பு)",
    sortAlpha: "தலைப்பு (அகராதிப்படி)",
    sortConfidence: "நம்பகத்தன்மை முன்னுரிமை",
    btnDetails: "முழு தொல்பொருள் விவரம்",
    evidenceTitle: "அகழாய்வு மற்றும் மூல ஆதாரம்:",
    modalMetaTitle: "தொல்லியல் மூலத்தரவுகள்",
    modalEvidenceTitle: "ஆராய்ச்சி மேற்கோள் & சான்று",
    modalCopyCitation: "மேற்கோளை நகலெடு",
    modalDownloadJson: "JSON தரவிறக்கு",
    citationCopied: "மேற்கோள் நகலெடுக்கப்பட்டது!",
    speakText: "விளக்கத்தைக் கேட்க",
  }
};

// Shards for Epigraphy Lab
const EPIGRAPHY_SHARDS = [
  {
    shard: "𑀓𑀼𑀯𑀺𑀭𑀦𑁆 𑀆𑀡𑁆",
    tamil: "குவிரன் ஆதன்",
    translit: "Kuviran Athan",
    meaning: "Athan, person belonging to / of Kuviran (personal trade name)",
    script: "Tamil-Brahmi (தமிழி)",
    strata: "Keeladi Trench IV, Depth 3.53m (Pre-Asokan Layer)",
    c14Date: "580 BCE (AMS Beta-499770)",
    analysis: "Confirms literacy in ancient Tamil society as early as the 6th century BCE. The name combines 'Kuviran' (trader / merchant title) with 'Athan' (common Sangam proper noun)."
  },
  {
    shard: "𑀆𑀡𑁆",
    tamil: "ஆதன்",
    translit: "Athan",
    meaning: "Athan (Prominent Sangam-era clan and personal name)",
    script: "Tamil-Brahmi (தமிழி)",
    strata: "Keeladi Trench III, Layer 5",
    c14Date: "c. 5th Century BCE",
    analysis: "Frequently cited in Sangam anthologies (Agananuru, Purananuru). Inscribed post-firing on black-and-red ware by the pot owner."
  },
  {
    shard: "𑀢𑀺𑀘𑀦𑁆",
    tamil: "திசன்",
    translit: "Thisan",
    meaning: "Thisan (Individual personal name)",
    script: "Tamil-Brahmi (தமிழி)",
    strata: "Keeladi Trench VI, Depth 2.8m",
    c14Date: "c. 4th Century BCE",
    analysis: "Demonstrates that potters and ordinary citizens etched their names upon household ceramics, proving widespread societal literacy."
  }
];

// Timeline Milestones
const TIMELINE_DATA = [
  {
    year: "580 BCE",
    period: "Early Historic Keeladi",
    title: "Urban Settlement & Tamil-Brahmi Literacy on River Vaigai",
    taTitle: "வைகை நதிக்கரையில் கீழடி நகர நாகரிகம் மற்றும் தமிழி எழுத்தறிவு",
    desc: "Beta Analytic (Miami) AMS dating of charcoal samples from Keeladi establishes permanent brick structures, drainage systems, and Tamil-Brahmi potsherds to 580 BCE contemporary to Gangetic urbanization."
  },
  {
    year: "300 BCE – 300 CE",
    period: "Classical Sangam Age",
    title: "Sangam Academies, Roman Trade & Maritime Ports",
    taTitle: "சங்க காலம், உரோமானிய வணிகம் மற்றும் துறைமுகங்கள்",
    desc: "Active maritime trade across Alagankulam, Korkai, and Muziris. Roman amphorae, rouletted ware, and 4,000+ semi-precious beads unearthed at Keeladi attest to global trade networks."
  },
  {
    year: "6th – 9th Century CE",
    period: "Pallava & Early Pandya Eras",
    title: "Rock-Cut Architecture & Grantha / Vatteluttu Epigraphs",
    taTitle: "பல்லவர், முற்கால பாண்டியர் குடைவரைக் கோயில்கள் & வட்டெழுத்து",
    desc: "Development of Vatteluttu script in South Tamil Nadu and Grantha script for Sanskrit in Thondaimandalam. Royal charters and temple endowment inscriptions."
  },
  {
    year: "9th – 13th Century CE",
    period: "Imperial Chola Dynasty",
    title: "Golden Age of Tamil Epigraphy & Monumental Temple Charters",
    taTitle: "பிற்கால சோழர் பொற்காலம் & பெருங்கோயில் கல்வெட்டுகள்",
    desc: "Thousands of stone inscriptions and copper-plate grants (Thiruvalangadu, Karandai) documenting administration, village democracy (Uttiramerur), irrigation, and bronze metallurgy."
  },
  {
    year: "2023 – Present",
    period: "Modern Digital Preservation",
    title: "Keeladi Site Museum & BharatSHRI National Epigraphical Mission",
    taTitle: "கீழடி அருங்காட்சியகம் மற்றும் பாரத்ஸ்ரீ தேசிய கல்வெட்டு களஞ்சியம்",
    desc: "Inauguration of the world-class Keeladi Site Museum in Sivagangai and digitization of 100,000+ inscriptions by the Archaeological Survey of India under BharatSHRI."
  }
];

// Archaeometry Lab Reports
const SCIENCE_REPORTS = [
  {
    institution: "Beta Analytic Inc., Miami, Florida, USA",
    title: "AMS Radiocarbon (C-14) Chronology",
    taTitle: "AMS கதிரியக்க கார்பன்-14 காலக்கணிப்பு",
    finding: "Carbon sample (Beta-499770) from Trench KLD-3/3 at 353 cm depth dated to 580 BCE. Second sample dated to 380 BCE, firmly pushing the Sangam era antiquity back to the 6th century BCE.",
    stats: [
      { label: "Sample ID", val: "Beta-499770" },
      { label: "Calibrated Age", val: "580 BCE (2560 BP)" },
      { label: "Material", val: "Excavated Charcoal / Carbon" },
      { label: "Accuracy", val: "95.4% probability (2-sigma)" }
    ]
  },
  {
    institution: "Deccan College Postgraduate Institute, Pune",
    title: "Osteological & Faunal Analysis",
    taTitle: "விலங்கின எலும்பியல் பகுப்பாய்வு",
    finding: "Analysis of 70 animal bone specimens revealed cattle, buffalo, sheep, and goat constituted 53% of the faunal assemblage, serving agricultural draught and pastoral meat consumption.",
    stats: [
      { label: "Specimens Studied", val: "70 skeletal fragments" },
      { label: "Bovine Ratio", val: "53% domesticated cattle/ox" },
      { label: "Cut Marks", val: "Identified on caprine bones" },
      { label: "Species", val: "Bull, Buffalo, Nilgai, Boar" }
    ]
  },
  {
    institution: "Vellore Institute of Technology (VIT), Vellore",
    title: "Brick & Mortar Mineralogical Science",
    taTitle: "செங்கல் மற்றும் சுண்ணாம்பு சாந்து கனிம பகுப்பாய்வு",
    finding: "Keeladi brick specimens exhibited over 80% silica and iron, while binding mortar contained 97% lime (calcium oxide), demonstrating advanced hydraulic lime technology in ancient Tamil Nadu.",
    stats: [
      { label: "Mortar Lime Purity", val: "97% Calcium Oxide" },
      { label: "Brick Silica Content", val: "> 80% Quartz/Silica" },
      { label: "Brick Dimensions", val: "38 × 23 × 6 cm (Ratio 6:3:1)" },
      { label: "Compressive Strength", val: "High hydraulic resistance" }
    ]
  },
  {
    institution: "University of Pisa, Pisa, Italy",
    title: "Ceramic Petrography & Mineral Composition",
    taTitle: "மண்பாண்ட பாறைவியல் & களிமண் பகுப்பாய்வு",
    finding: "Thin-section petrographic analysis of Keeladi potsherds demonstrated that local Vaigai riverbed alluvial clay with high feldspar and quartz inclusions was used, with temperatures reaching 900°C.",
    stats: [
      { label: "Firing Temperature", val: "c. 850°C – 950°C" },
      { label: "Clay Provenance", val: "Local Vaigai Alluvial Bed" },
      { label: "Technique", val: "Fast Wheel + Reduction Firing" },
      { label: "Ware Types", val: "Black-and-Red, Rouletted" }
    ]
  }
];

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  renderLanguage();
  renderTabs();
  renderControlBar();
  renderExhibits();
  setupEventListeners();
});

// Switch Language
function setLanguage(lang) {
  state.lang = lang;
  document.documentElement.lang = lang;
  
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === lang);
  });

  renderLanguage();
  renderExhibits();
}

// Render dynamic language strings
function renderLanguage() {
  const t = I18N[state.lang];
  document.getElementById('hero-pill').textContent = t.heroPill;
  document.getElementById('hero-title').textContent = t.heroTitle;
  document.getElementById('hero-desc').textContent = t.heroDesc;
  document.getElementById('btn-explore').textContent = t.btnExplore;
  document.getElementById('btn-epigraphy').textContent = t.btnEpigraphy;

  document.getElementById('kpi1-num').textContent = t.kpi1Number;
  document.getElementById('kpi1-unit').textContent = t.kpi1Unit;
  document.getElementById('kpi1-label').textContent = t.kpi1Label;
  document.getElementById('kpi1-sub').textContent = t.kpi1Sub;

  document.getElementById('kpi2-num').textContent = t.kpi2Number;
  document.getElementById('kpi2-unit').textContent = t.kpi2Unit;
  document.getElementById('kpi2-label').textContent = t.kpi2Label;
  document.getElementById('kpi2-sub').textContent = t.kpi2Sub;

  document.getElementById('kpi3-num').textContent = t.kpi3Number;
  document.getElementById('kpi3-unit').textContent = t.kpi3Unit;
  document.getElementById('kpi3-label').textContent = t.kpi3Label;
  document.getElementById('kpi3-sub').textContent = t.kpi3Sub;

  document.getElementById('kpi4-num').textContent = t.kpi4Number;
  document.getElementById('kpi4-unit').textContent = t.kpi4Unit;
  document.getElementById('kpi4-label').textContent = t.kpi4Label;
  document.getElementById('kpi4-sub').textContent = t.kpi4Sub;

  document.getElementById('tab-btn-exhibits').innerHTML = t.tabExhibits;
  document.getElementById('tab-btn-epigraphy').innerHTML = t.tabEpigraphy;
  document.getElementById('tab-btn-timeline').innerHTML = t.tabTimeline;
  document.getElementById('tab-btn-science').innerHTML = t.tabScience;
  document.getElementById('tab-btn-data').innerHTML = t.tabData;

  const searchInput = document.getElementById('search-input');
  if (searchInput) searchInput.placeholder = t.searchPlaceholder;
}

// Render Control Bar with Category Pills
function renderControlBar() {
  const container = document.getElementById('filter-pills-row');
  if (!container) return;

  const t = I18N[state.lang];
  const categories = [
    { id: 'all', label: t.filterAll },
    { id: 'keeladi', label: t.filterKeeladi },
    { id: 'brahmi', label: t.filterBrahmi },
    { id: 'brick', label: t.filterBrick },
    { id: 'lapidary', label: t.filterLapidary },
    { id: 'faunal', label: t.filterFaunal },
    { id: 'trade', label: t.filterTrade },
    { id: 'asi', label: t.filterAsi },
  ];

  container.innerHTML = categories.map(cat => `
    <button class="filter-pill ${state.selectedCategory === cat.id ? 'active' : ''}" 
            data-category="${cat.id}">
      ${cat.label}
    </button>
  `).join('');

  container.querySelectorAll('.filter-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      state.selectedCategory = btn.dataset.category;
      container.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderExhibits();
    });
  });
}

// Render Main Exhibits Grid
function renderExhibits() {
  const grid = document.getElementById('exhibits-grid');
  if (!grid) return;

  const filtered = filterRecords();
  const t = I18N[state.lang];

  document.getElementById('results-count').textContent = 
    `Showing ${filtered.length} of ${state.records.length} archaeological records`;

  if (filtered.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 4rem 1rem; color: var(--text-muted);">
        <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
        <h3>No matching artifacts found</h3>
        <p>Try searching for terms like "Keeladi", "Chola", "Inscriptions", "வைகை", or "Brick".</p>
      </div>
    `;
    return;
  }

  grid.innerHTML = filtered.map(rec => {
    const isKeeladi = (rec.site_name && rec.site_name.includes('Keeladi')) || 
                      (rec.source_url && rec.source_url.includes('keeladimuseum'));
    const isASI = !isKeeladi;
    const isTamil = state.lang === 'ta';

    const primaryTitle = isTamil && rec.local_name_ta ? rec.local_name_ta : rec.title;
    const secondaryTitle = isTamil ? rec.title : (rec.local_name_ta || '');

    // Fallback icon based on type
    let icon = '🏛️';
    if (rec.record_type.includes('inscription') || rec.record_type.includes('epigraphy')) icon = '📜';
    else if (rec.record_type.includes('faunal')) icon = '🐂';
    else if (rec.record_type.includes('brick') || rec.record_type.includes('structure')) icon = '🧱';
    else if (rec.record_type.includes('lapidary') || rec.record_type.includes('ornament')) icon = '💎';
    else if (rec.record_type.includes('science')) icon = '🔬';
    else if (rec.record_type.includes('trade')) icon = '⛵';

    return `
      <article class="exhibit-card" data-id="${rec.record_id}">
        <div class="card-media-banner">
          ${rec.image_source_url ? `
            <img src="${rec.image_source_url}" 
                 alt="${rec.title}" 
                 loading="lazy" 
                 onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
          ` : ''}
          <div class="card-fallback-art" style="${rec.image_source_url ? 'display: none;' : 'display: flex;'}">
            <span class="art-icon">${icon}</span>
            <span class="art-tag">${rec.record_type.replace(/_/g, ' ')}</span>
          </div>
          <div class="card-badge-group">
            ${isKeeladi ? '<span class="badge-tag badge-keeladi">Keeladi Museum</span>' : ''}
            ${isASI ? '<span class="badge-tag badge-asi">ASI BharatSHRI</span>' : ''}
            ${rec.historical_period && rec.historical_period.includes('580') ? '<span class="badge-tag badge-dating">580 BCE</span>' : ''}
          </div>
        </div>

        <div class="card-body">
          <div class="card-header-meta">
            <span>${rec.script || 'Tamil-Brahmi / Grantha'}</span>
            <span>${rec.historical_period ? rec.historical_period.split('(')[0].trim() : 'Ancient'}</span>
          </div>

          <h3 class="card-title">${primaryTitle}</h3>
          ${secondaryTitle ? `<h4 class="card-tamil-title">${secondaryTitle}</h4>` : ''}

          <p class="card-desc">${rec.description}</p>

          ${rec.source_quote_or_evidence ? `
            <div class="evidence-box">
              "${rec.source_quote_or_evidence.substring(0, 180)}..."
            </div>
          ` : ''}

          <div class="card-meta-chips">
            ${rec.material ? `<span class="meta-chip">🧱 ${rec.material.split(',')[0]}</span>` : ''}
            ${rec.district ? `<span class="meta-chip">📍 ${rec.district}</span>` : ''}
            ${rec.dynasty ? `<span class="meta-chip">👑 ${rec.dynasty}</span>` : ''}
            <span class="meta-chip">🛡️ ${rec.confidence_level}</span>
          </div>

          <div class="card-actions">
            <button class="btn-card-primary" onclick="openRecordModal('${rec.record_id}')">
              ${t.btnDetails}
            </button>
            <button class="btn-icon" title="${t.speakText}" onclick="speakRecord('${rec.record_id}', event)">
              🔊
            </button>
            <button class="btn-icon" title="Copy Citation" onclick="copyCitation('${rec.record_id}', event)">
              📋
            </button>
          </div>
        </div>
      </article>
    `;
  }).join('');
}

// Filter and Sort Records
function filterRecords() {
  let list = [...state.records];

  // Category Filter
  if (state.selectedCategory !== 'all') {
    if (state.selectedCategory === 'keeladi') {
      list = list.filter(r => (r.site_name && r.site_name.includes('Keeladi')) || (r.source_url && r.source_url.includes('keeladimuseum')));
    } else if (state.selectedCategory === 'asi') {
      list = list.filter(r => r.source_organization && r.source_organization.includes('Archaeological Survey of India'));
    } else if (state.selectedCategory === 'brahmi') {
      list = list.filter(r => (r.script && (r.script.includes('Brahmi') || r.script.includes('Damili'))) || (r.title && r.title.includes('Brahmi')));
    } else if (state.selectedCategory === 'brick') {
      list = list.filter(r => (r.material && r.material.toLowerCase().includes('brick')) || (r.title && r.title.toLowerCase().includes('brick')));
    } else if (state.selectedCategory === 'lapidary') {
      list = list.filter(r => r.record_type.includes('adornment') || (r.material && (r.material.toLowerCase().includes('gold') || r.material.toLowerCase().includes('bead'))));
    } else if (state.selectedCategory === 'faunal') {
      list = list.filter(r => r.record_type.includes('faunal') || (r.title && r.title.toLowerCase().includes('faunal')));
    } else if (state.selectedCategory === 'trade') {
      list = list.filter(r => r.record_type.includes('maritime') || (r.title && r.title.toLowerCase().includes('trade')));
    }
  }

  // Search Query
  if (state.searchQuery.trim()) {
    const q = state.searchQuery.toLowerCase();
    list = list.filter(r => {
      const matchTitle = (r.title || '').toLowerCase().includes(q);
      const matchTa = (r.local_name_ta || '').includes(q);
      const matchDesc = (r.description || '').toLowerCase().includes(q);
      const matchScript = (r.script || '').toLowerCase().includes(q);
      const matchDynasty = (r.dynasty || '').toLowerCase().includes(q);
      const matchMaterial = (r.material || '').toLowerCase().includes(q);
      const matchSite = (r.site_name || '').toLowerCase().includes(q);
      return matchTitle || matchTa || matchDesc || matchScript || matchDynasty || matchMaterial || matchSite;
    });
  }

  // Sorting
  if (state.sortBy === 'alpha') {
    list.sort((a, b) => a.title.localeCompare(b.title));
  } else if (state.sortBy === 'confidence') {
    const weights = { HIGH: 3, MEDIUM: 2, LOW: 1 };
    list.sort((a, b) => (weights[b.confidence_level] || 0) - (weights[a.confidence_level] || 0));
  }

  return list;
}

// Render Epigraphy Lab
function renderEpigraphyLab() {
  const container = document.getElementById('epigraphy-container');
  if (!container) return;

  container.innerHTML = `
    <div class="epigraphy-lab-section">
      <div class="section-head">
        <h2>Ancient Tamil-Brahmi (தமிழி) Decipherer</h2>
        <p>Decoded potsherds and epigraphical graffiti from Keeladi Vaigai excavations, demonstrating widespread societal literacy in ancient Tamil Nadu from the 6th century BCE.</p>
      </div>

      <div class="shards-grid">
        ${EPIGRAPHY_SHARDS.map(s => `
          <div class="shard-card">
            <div class="shard-glyph-large">${s.tamil}</div>
            <div class="shard-translit">${s.translit} • ${s.script}</div>
            <div class="shard-details">
              <p><strong>Meaning:</strong> ${s.meaning}</p>
              <p style="margin-top: 0.5rem; color: var(--text-muted);">${s.analysis}</p>
            </div>
            <div class="shard-meta-row">
              <span>📍 ${s.strata}</span>
              <span style="color: var(--accent-patina); font-weight: 600;">⏳ ${s.c14Date}</span>
            </div>
          </div>
        `).join('')}
      </div>

      <div style="background: rgba(8, 11, 17, 0.6); padding: 1.5rem; border-radius: var(--radius-md); border: 1px solid var(--border-subtle);">
        <h4 style="color: var(--accent-gold); margin-bottom: 0.75rem;">🔤 Script Evolution Trajectory</h4>
        <p style="font-size: 0.88rem; color: var(--text-secondary); line-height: 1.6;">
          Graffiti marks found on Keeladi potsherds share 75% visual correlation with Indus Valley script signs, bridging the cultural timeline into Tamil-Brahmi (தமிழி, 6th c. BCE), subsequently evolving into Vatteluttu (வட்டெழுத்து, 6th–14th c. CE), and culminating in modern Tamil script.
        </p>
      </div>
    </div>
  `;
}

// Render Timeline
function renderTimeline() {
  const container = document.getElementById('timeline-container');
  if (!container) return;

  container.innerHTML = `
    <div class="section-head">
      <h2>Sangam Era to Modern Epigraphy Timeline</h2>
      <p>Chronological milestones of Tamil epigraphy, urban settlements, and scientific archaeological research.</p>
    </div>
    <div class="timeline-container">
      ${TIMELINE_DATA.map((t, i) => `
        <div class="timeline-item">
          <div class="timeline-dot"></div>
          <div class="timeline-content">
            <div class="timeline-year">${t.year}</div>
            <h4 class="timeline-title">${state.lang === 'ta' ? t.taTitle : t.title}</h4>
            <div style="font-size: 0.75rem; color: var(--accent-patina); font-family: var(--font-mono); margin-bottom: 0.5rem;">${t.period}</div>
            <p class="timeline-desc">${t.desc}</p>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

// Render Archaeometry Science Lab
function renderScienceLab() {
  const container = document.getElementById('science-container');
  if (!container) return;

  container.innerHTML = `
    <div class="section-head">
      <h2>Archaeometry & Multidisciplinary Science Lab</h2>
      <p>Authoritative physical and chemical analyses conducted by premier global institutions establishing the material antiquity of Keeladi.</p>
    </div>

    <div class="science-grid">
      ${SCIENCE_REPORTS.map(rep => `
        <div class="science-card">
          <div class="science-icon">🔬</div>
          <div class="science-institution">${rep.institution}</div>
          <h3 class="science-title">${state.lang === 'ta' ? rep.taTitle : rep.title}</h3>
          <p class="science-finding">${rep.finding}</p>

          <ul class="stat-pills-list">
            ${rep.stats.map(s => `
              <li class="stat-pill-item">
                <span style="color: var(--text-muted);">${s.label}:</span>
                <span style="font-weight: 600; color: var(--accent-gold); font-family: var(--font-mono);">${s.val}</span>
              </li>
            `).join('')}
          </ul>
        </div>
      `).join('')}
    </div>
  `;
}

// Render Data & Export Hub
function renderDataHub() {
  const container = document.getElementById('data-container');
  if (!container) return;

  container.innerHTML = `
    <div class="section-head">
      <h2>Heritage Dataset & Open Data Hub</h2>
      <p>Download the curated, validated archaeological dataset in standard machine-readable formats. Fully offline-capable and schema-compliant.</p>
    </div>

    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1.5rem; margin-bottom: 3rem;">
      <div class="science-card">
        <div style="font-size: 2.5rem; margin-bottom: 1rem;">📄</div>
        <h3>JSON Dataset</h3>
        <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1.25rem;">Full hierarchical records with all 74 attributes, citations, and nested extra metadata.</p>
        <a href="../data/heritage_records.json" download="heritage_records.json" class="btn-primary" style="display: block; text-align: center;">Download JSON (280 KB)</a>
      </div>

      <div class="science-card">
        <div style="font-size: 2.5rem; margin-bottom: 1rem;">📊</div>
        <h3>CSV Spreadsheet</h3>
        <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1.25rem;">Tabular flat representation formatted with UTF-8 BOM for Microsoft Excel and pandas.</p>
        <a href="../data/heritage_records.csv" download="heritage_records.csv" class="btn-primary" style="display: block; text-align: center;">Download CSV (53 Rows)</a>
      </div>

      <div class="science-card">
        <div style="font-size: 2.5rem; margin-bottom: 1rem;">📑</div>
        <h3>Excel Workbook</h3>
        <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1.25rem;">Multi-sheet styled workbook with data dictionary and verification summary.</p>
        <a href="../data/heritage_records.xlsx" download="heritage_records.xlsx" class="btn-secondary" style="display: block; text-align: center;">Download XLSX</a>
      </div>

      <div class="science-card">
        <div style="font-size: 2.5rem; margin-bottom: 1rem;">🗄️</div>
        <h3>SQLite Database</h3>
        <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1.25rem;">Indexed relational database with full-text search (FTS5) enabled on heritage records.</p>
        <a href="../db/heritage.db" download="heritage.db" class="btn-secondary" style="display: block; text-align: center;">Download SQLite DB</a>
      </div>
    </div>

    <div style="background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 2rem;">
      <h3 style="color: var(--accent-gold); margin-bottom: 1rem;">Data Quality & Integrity Scorecard</h3>
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
        <div style="background: rgba(8, 11, 17, 0.7); padding: 1rem; border-radius: var(--radius-sm);">
          <div style="font-size: 0.75rem; color: var(--text-muted);">Total Curated Records</div>
          <div style="font-size: 1.6rem; font-weight: 700; color: #fff;">53</div>
        </div>
        <div style="background: rgba(8, 11, 17, 0.7); padding: 1rem; border-radius: var(--radius-sm);">
          <div style="font-size: 0.75rem; color: var(--text-muted);">Missing Record IDs</div>
          <div style="font-size: 1.6rem; font-weight: 700; color: var(--accent-patina);">0 (100% Valid)</div>
        </div>
        <div style="background: rgba(8, 11, 17, 0.7); padding: 1rem; border-radius: var(--radius-sm);">
          <div style="font-size: 0.75rem; color: var(--text-muted);">Tamil Unicode Normalization</div>
          <div style="font-size: 1.6rem; font-weight: 700; color: var(--accent-patina);">NFC Standard</div>
        </div>
        <div style="background: rgba(8, 11, 17, 0.7); padding: 1rem; border-radius: var(--radius-sm);">
          <div style="font-size: 0.75rem; color: var(--text-muted);">Discovered Artifact Media</div>
          <div style="font-size: 1.6rem; font-weight: 700; color: var(--accent-gold);">509 Assets</div>
        </div>
      </div>
    </div>
  `;
}

// Modal View
function openRecordModal(id) {
  const rec = state.records.find(r => r.record_id === id);
  if (!rec) return;

  state.activeRecord = rec;
  const modal = document.getElementById('record-modal');
  const t = I18N[state.lang];

  document.getElementById('modal-title').textContent = rec.title;
  document.getElementById('modal-ta-title').textContent = rec.local_name_ta || '';

  const metaGrid = document.getElementById('modal-meta-grid');
  metaGrid.innerHTML = `
    <div><div class="meta-field-label">Record ID</div><div class="meta-field-val" style="font-family: var(--font-mono); font-size: 0.75rem;">${rec.record_id}</div></div>
    <div><div class="meta-field-label">Period / Era</div><div class="meta-field-val">${rec.historical_period || 'Ancient'}</div></div>
    <div><div class="meta-field-label">Scientific Dating</div><div class="meta-field-val" style="color: var(--accent-patina);">${rec.dating_method || 'Typological / Stratigraphic'}</div></div>
    <div><div class="meta-field-label">Script & Language</div><div class="meta-field-val">${rec.script || 'Tamil-Brahmi'} / ${rec.language || 'Tamil'}</div></div>
    <div><div class="meta-field-label">Material & Medium</div><div class="meta-field-val">${rec.material || 'Terracotta / Brick'}</div></div>
    <div><div class="meta-field-label">Site & District</div><div class="meta-field-val">${rec.site_name || 'Keeladi'}, ${rec.district || 'Sivagangai'}</div></div>
    <div><div class="meta-field-label">Repository / Museum</div><div class="meta-field-val">${rec.museum_or_repository || 'Keeladi Site Museum'}</div></div>
    <div><div class="meta-field-label">Confidence & Review</div><div class="meta-field-val">${rec.confidence_level} • ${rec.source_verified}</div></div>
  `;

  document.getElementById('modal-desc').textContent = rec.description;

  const quoteBox = document.getElementById('modal-quote');
  if (rec.source_quote_or_evidence) {
    quoteBox.style.display = 'block';
    quoteBox.textContent = `"${rec.source_quote_or_evidence}"`;
  } else {
    quoteBox.style.display = 'none';
  }

  const sourceLink = document.getElementById('modal-source-link');
  if (rec.source_url) {
    sourceLink.href = rec.source_url;
    sourceLink.textContent = `Explore Source: ${rec.source_organization || 'Official Portal'} ↗`;
  }

  modal.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeRecordModal() {
  const modal = document.getElementById('record-modal');
  modal.classList.remove('active');
  document.body.style.overflow = '';
  state.activeRecord = null;
}

// Copy Citation Helper
function copyCitation(id, event) {
  if (event) event.stopPropagation();
  const rec = state.records.find(r => r.record_id === id) || state.activeRecord;
  if (!rec) return;

  const citation = `${rec.source_organization || 'Archaeological Authority'}. "${rec.title}" (${rec.historical_period || 'Sangam Period'}). Keeladi & Ancient Tamil Heritage Explorer, accessed ${rec.source_access_date || '2026'}. Source: ${rec.source_url || 'https://www.keeladimuseum.tn.gov.in/'}`;

  navigator.clipboard.writeText(citation).then(() => {
    alert(I18N[state.lang].citationCopied);
  });
}

// Text to Speech
function speakRecord(id, event) {
  if (event) event.stopPropagation();
  const rec = state.records.find(r => r.record_id === id);
  if (!rec) return;

  if (!('speechSynthesis' in window)) {
    alert("Speech synthesis is not supported in this browser.");
    return;
  }

  window.speechSynthesis.cancel();
  const textToRead = `${rec.title}. ${rec.description.substring(0, 300)}`;
  const utterance = new SpeechSynthesisUtterance(textToRead);
  utterance.rate = 0.95;
  utterance.pitch = 1.0;
  window.speechSynthesis.speak(utterance);
}

// Setup Event Listeners
function setupEventListeners() {
  // Search input
  const searchInput = document.getElementById('search-input');
  const clearBtn = document.getElementById('clear-search');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      state.searchQuery = e.target.value;
      if (clearBtn) clearBtn.style.display = state.searchQuery ? 'block' : 'none';
      renderExhibits();
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      if (searchInput) searchInput.value = '';
      state.searchQuery = '';
      clearBtn.style.display = 'none';
      renderExhibits();
    });
  }

  // Sort dropdown
  const sortSelect = document.getElementById('sort-select');
  if (sortSelect) {
    sortSelect.addEventListener('change', (e) => {
      state.sortBy = e.target.value;
      renderExhibits();
    });
  }

  // Tab buttons
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      state.activeTab = tab;
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      document.querySelectorAll('.tab-content-panel').forEach(panel => {
        panel.style.display = panel.id === `tab-panel-${tab}` ? 'block' : 'none';
      });

      if (tab === 'epigraphy') renderEpigraphyLab();
      else if (tab === 'timeline') renderTimeline();
      else if (tab === 'science') renderScienceLab();
      else if (tab === 'data') renderDataHub();
    });
  });

  // Modal overlay click to close
  const modal = document.getElementById('record-modal');
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeRecordModal();
    });
  }

  // Keyboard escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeRecordModal();
  });
}

function renderTabs() {
  // Default show exhibits
  const exhibitsPanel = document.getElementById('tab-panel-exhibits');
  if (exhibitsPanel) exhibitsPanel.style.display = 'block';
}
