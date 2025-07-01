/**
 * Mobile-First JavaScript Enhancement for Hospital Equipment Management System
 * Provides touch-friendly interactions, pull-to-refresh, swipe gestures, and mobile UX
 */

class MobileEnhancement {
  constructor() {
    this.init();
    this.setupEventListeners();
    this.setupTouchGestures();
    this.setupPullToRefresh();
  }

  init() {
    // Add mobile-specific body classes
    document.body.classList.add('mobile-enhanced');
    
    // Add viewport meta tag if missing
    if (!document.querySelector('meta[name="viewport"]')) {
      const viewport = document.createElement('meta');
      viewport.name = 'viewport';
      viewport.content = 'width=device-width, initial-scale=1.0, user-scalable=no';
      document.head.appendChild(viewport);
    }

    // Initialize mobile detection
    this.isMobile = window.innerWidth <= 768;
    this.isTablet = window.innerWidth > 768 && window.innerWidth <= 1024;
    this.isTouchDevice = 'ontouchstart' in window;

    // Convert tables to mobile cards on small screens
    this.convertTablesToCards();
    
    // Setup mobile navigation
    this.setupMobileNavigation();
  }

  setupEventListeners() {
    // Window resize handler
    window.addEventListener('resize', () => {
      this.isMobile = window.innerWidth <= 768;
      this.convertTablesToCards();
    });

    // Touch-friendly form enhancements
    this.enhanceForms();
    
    // Better button interactions
    this.enhanceButtons();
  }

  setupMobileNavigation() {
    // Enhanced mobile navbar collapse
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
      navbarToggler.addEventListener('click', () => {
        // Add smooth animation
        navbarCollapse.style.transition = 'all 0.3s ease';
      });

      // Close navbar when clicking on nav links (mobile)
      const navLinks = document.querySelectorAll('.nav-link');
      navLinks.forEach(link => {
        link.addEventListener('click', () => {
          if (this.isMobile && navbarCollapse.classList.contains('show')) {
            navbarToggler.click();
          }
        });
      });
    }
  }

  convertTablesToCards() {
    if (!this.isMobile) return;

    const tables = document.querySelectorAll('.equipment-table');
    tables.forEach(table => {
      if (table.dataset.mobileConverted) return;
      
      const tbody = table.querySelector('tbody');
      if (!tbody) return;

      // Create mobile cards container
      const cardsContainer = document.createElement('div');
      cardsContainer.className = 'mobile-equipment-cards d-block d-md-none';
      
      // Convert each row to a card
      const rows = tbody.querySelectorAll('tr');
      rows.forEach(row => {
        const card = this.createEquipmentCard(row, table);
        if (card) cardsContainer.appendChild(card);
      });

      // Insert cards after table
      table.closest('.table-responsive').appendChild(cardsContainer);
      table.dataset.mobileConverted = 'true';
    });
  }

  createEquipmentCard(row, table) {
    const cells = row.querySelectorAll('td');
    if (cells.length === 0) return null;

    const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim());
    
    const card = document.createElement('div');
    card.className = 'equipment-card';
    
    // Equipment name and status header
    const name = cells[1]?.textContent?.trim() || 'Unknown Equipment';
    const status = this.getStatusFromRow(cells);
    
    card.innerHTML = `
      <div class="equipment-card-header">
        <div class="equipment-name">${name}</div>
        <div class="equipment-status">${status}</div>
      </div>
      <div class="equipment-details">
        ${this.createEquipmentDetails(cells, headers)}
      </div>
      <div class="equipment-actions">
        ${this.createEquipmentActions(row)}
      </div>
    `;

    return card;
  }

  createEquipmentDetails(cells, headers) {
    let details = '';
    const importantFields = [
      'Department', 'Model', 'Serial Number', 'Manufacturer', 
      'Installation Date', 'Warranty End', 'Log Number'
    ];

    cells.forEach((cell, index) => {
      const header = headers[index];
      const value = cell.textContent.trim();
      
      if (importantFields.some(field => header.includes(field)) && value) {
        details += `
          <div class="equipment-detail">
            <div class="equipment-detail-label">${header}</div>
            <div class="equipment-detail-value">${value}</div>
          </div>
        `;
      }
    });

    return details;
  }

  createEquipmentActions(row) {
    const actionButtons = row.querySelectorAll('a, button');
    let actions = '';
    
    actionButtons.forEach(button => {
      const text = button.textContent.trim();
      const href = button.getAttribute('href') || '#';
      const classes = button.className;
      
      if (text && !text.includes('Select')) {
        actions += `
          <a href="${href}" class="btn btn-sm ${classes.includes('btn-primary') ? 'btn-primary' : 'btn-outline-primary'}">
            ${text}
          </a>
        `;
      }
    });

    return actions;
  }

  getStatusFromRow(cells) {
    // Look for status badge or status information
    for (let cell of cells) {
      const badge = cell.querySelector('.badge');
      if (badge) {
        return badge.outerHTML;
      }
      
      // Check for status-like content
      const text = cell.textContent.trim().toLowerCase();
      if (text.includes('overdue') || text.includes('upcoming') || text.includes('maintained')) {
        const statusClass = text.includes('overdue') ? 'danger' : 
                           text.includes('upcoming') ? 'warning' : 'success';
        return `<span class="badge bg-${statusClass}">${text}</span>`;
      }
    }
    return '<span class="badge bg-secondary">Unknown</span>';
  }

  enhanceForms() {
    // Add touch-friendly styling to form elements
    const formControls = document.querySelectorAll('.form-control, .form-select');
    formControls.forEach(control => {
      control.classList.add('mobile-touch-target');
      
      // Prevent zoom on iOS
      if (control.type !== 'email' && control.type !== 'url') {
        control.addEventListener('focus', () => {
          if (this.isMobile) {
            control.style.fontSize = '16px';
          }
        });
      }
    });

    // Enhanced date picker for mobile
    this.enhanceDatePickers();
  }

  enhanceDatePickers() {
    const datePickers = document.querySelectorAll('.modern-date-picker');
    datePickers.forEach(picker => {
      if (this.isMobile) {
        // Use native date picker on mobile
        picker.type = 'date';
        picker.classList.add('mobile-native-date');
      }
    });
  }

  enhanceButtons() {
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
      button.classList.add('mobile-touch-target');
      
      // Add ripple effect
      button.addEventListener('click', (e) => {
        this.createRippleEffect(e, button);
      });
    });
  }

  createRippleEffect(event, element) {
    const ripple = document.createElement('span');
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;
    
    ripple.style.cssText = `
      position: absolute;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.6);
      width: ${size}px;
      height: ${size}px;
      left: ${x}px;
      top: ${y}px;
      animation: ripple 0.6s ease-out;
      pointer-events: none;
    `;
    
    // Add ripple keyframes if not exists
    if (!document.querySelector('#ripple-style')) {
      const style = document.createElement('style');
      style.id = 'ripple-style';
      style.textContent = `
        @keyframes ripple {
          0% { transform: scale(0); opacity: 1; }
          100% { transform: scale(2); opacity: 0; }
        }
      `;
      document.head.appendChild(style);
    }
    
    element.style.position = 'relative';
    element.style.overflow = 'hidden';
    element.appendChild(ripple);
    
    setTimeout(() => ripple.remove(), 600);
  }

  setupTouchGestures() {
    if (!this.isTouchDevice) return;

    // Setup swipe gestures for equipment cards
    this.setupSwipeGestures();
    
    // Setup pinch-to-zoom for tables (optional)
    this.setupPinchToZoom();
  }

  setupSwipeGestures() {
    let startX, startY, currentX, currentY;
    
    document.addEventListener('touchstart', (e) => {
      const touch = e.touches[0];
      startX = touch.clientX;
      startY = touch.clientY;
    });

    document.addEventListener('touchmove', (e) => {
      if (!startX || !startY) return;
      
      currentX = e.touches[0].clientX;
      currentY = e.touches[0].clientY;
      
      const diffX = startX - currentX;
      const diffY = startY - currentY;
      
      // Detect horizontal swipe on equipment cards
      const card = e.target.closest('.equipment-card');
      if (card && Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
        if (diffX > 0) {
          // Swipe left - show actions
          card.classList.add('swiped');
        } else {
          // Swipe right - hide actions
          card.classList.remove('swiped');
        }
      }
    });

    document.addEventListener('touchend', () => {
      startX = startY = currentX = currentY = null;
    });
  }

  setupPinchToZoom() {
    // Optional: Allow pinch-to-zoom on complex tables
    const tables = document.querySelectorAll('.table-responsive');
    tables.forEach(table => {
      table.style.touchAction = 'pan-x pan-y pinch-zoom';
    });
  }

  setupPullToRefresh() {
    if (!this.isTouchDevice || !this.isMobile) return;

    let startY = 0;
    let currentY = 0;
    let isPulling = false;
    
    const refreshThreshold = 80;
    const mainContent = document.querySelector('.main-content') || document.body;
    
    // Create refresh indicator
    const indicator = document.createElement('div');
    indicator.className = 'pull-to-refresh-indicator';
    indicator.innerHTML = '<i class="fas fa-sync-alt"></i>';
    indicator.style.display = 'none';
    mainContent.prepend(indicator);

    document.addEventListener('touchstart', (e) => {
      if (window.scrollY === 0) {
        startY = e.touches[0].clientY;
        isPulling = true;
      }
    });

    document.addEventListener('touchmove', (e) => {
      if (!isPulling) return;
      
      currentY = e.touches[0].clientY;
      const pullDistance = currentY - startY;
      
      if (pullDistance > 0 && pullDistance < refreshThreshold * 2) {
        e.preventDefault();
        indicator.style.display = 'flex';
        indicator.style.top = `${Math.min(pullDistance - 60, 20)}px`;
        
        if (pullDistance > refreshThreshold) {
          mainContent.classList.add('pull-to-refresh');
          indicator.classList.add('ready');
        } else {
          mainContent.classList.remove('pull-to-refresh');
          indicator.classList.remove('ready');
        }
      }
    });

    document.addEventListener('touchend', () => {
      if (!isPulling) return;
      
      const pullDistance = currentY - startY;
      
      if (pullDistance > refreshThreshold) {
        // Trigger refresh
        this.triggerRefresh();
      }
      
      // Reset
      indicator.style.display = 'none';
      mainContent.classList.remove('pull-to-refresh');
      indicator.classList.remove('ready');
      isPulling = false;
      startY = currentY = 0;
    });
  }

  triggerRefresh() {
    // Show loading indicator
    const indicator = document.querySelector('.pull-to-refresh-indicator');
    if (indicator) {
      indicator.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
      indicator.style.display = 'flex';
      indicator.style.top = '20px';
    }

    // Simulate refresh or trigger actual refresh
    setTimeout(() => {
      window.location.reload();
    }, 500);
  }

  // Utility function to show mobile toast notifications
  showMobileToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `mobile-toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
      position: fixed;
      bottom: 20px;
      left: 50%;
      transform: translateX(-50%);
      background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#667eea'};
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      z-index: 1070;
      font-size: 0.9rem;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      animation: slideUp 0.3s ease;
    `;

    document.body.appendChild(toast);
    
    setTimeout(() => {
      toast.style.animation = 'slideDown 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  // Initialize mobile-specific features for equipment lists
  initEquipmentListMobile() {
    if (!this.isMobile) return;

    // Add mobile search enhancement
    const searchInput = document.querySelector('#searchInput');
    if (searchInput) {
      searchInput.placeholder = 'Search...';
      searchInput.style.marginBottom = '12px';
    }

    // Stack filter controls
    const filterControls = document.querySelectorAll('#statusFilter, #typeFilter');
    filterControls.forEach(control => {
      control.style.width = '100%';
      control.style.marginBottom = '8px';
    });
  }
}

// Initialize mobile enhancements when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.mobileEnhancement = new MobileEnhancement();
  
  // Initialize equipment list mobile features if on equipment page
  if (document.querySelector('.equipment-table')) {
    window.mobileEnhancement.initEquipmentListMobile();
  }
});

// Add CSS animations for mobile interactions
const mobileStyles = document.createElement('style');
mobileStyles.textContent = `
  @keyframes slideUp {
    from { transform: translateX(-50%) translateY(100%); opacity: 0; }
    to { transform: translateX(-50%) translateY(0); opacity: 1; }
  }
  
  @keyframes slideDown {
    from { transform: translateX(-50%) translateY(0); opacity: 1; }
    to { transform: translateX(-50%) translateY(100%); opacity: 0; }
  }
  
  .mobile-enhanced .table-responsive table {
    transition: opacity 0.3s ease;
  }
  
  @media (max-width: 768px) {
    .mobile-enhanced .table-responsive table {
      opacity: 0;
      height: 0;
      overflow: hidden;
    }
  }
`;
document.head.appendChild(mobileStyles); 