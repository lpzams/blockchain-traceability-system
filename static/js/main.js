// ===== 区块链溯源系统 - 增强版 JavaScript =====

// ===== 配置 =====
const CONFIG = {
    refreshInterval: 30000, // 30秒自动刷新
    chartColors: {
        primary: '#3b82f6',
        secondary: '#14b8a6',
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444',
        info: '#06b6d4'
    },
    animationDuration: 300
};

// ===== 全局状态管理 =====
const AppState = {
    charts: {},
    intervals: {},
    wsConnections: {}
};

// ===== 工具函数 =====

// 显示加载状态
function showLoading(element) {
    if (!element) return;

    if (element.tagName === 'BUTTON') {
        element.disabled = true;
        element.dataset.originalContent = element.innerHTML;
        element.innerHTML = '<span class="spinner me-2"></span> 处理中...';
        element.classList.add('loading');
    } else {
        element.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-lg mb-3"></div>
                <p class="text-muted">加载中...</p>
            </div>
        `;
    }
}

// 隐藏加载状态
function hideLoading(element) {
    if (!element) return;

    if (element.tagName === 'BUTTON' && element.dataset.originalContent) {
        element.disabled = false;
        element.innerHTML = element.dataset.originalContent;
        element.classList.remove('loading');
        delete element.dataset.originalContent;
    }
}

// 显示通知
function showNotification(message, type = 'info', duration = 5000) {
    const icons = {
        success: '<i class="fas fa-check-circle"></i>',
        danger: '<i class="fas fa-exclamation-circle"></i>',
        warning: '<i class="fas fa-exclamation-triangle"></i>',
        info: '<i class="fas fa-info-circle"></i>'
    };

    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show slide-in-down`;
    alert.innerHTML = `
        ${icons[type] || icons.info}
        <span class="ms-2">${message}</span>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alert, container.firstChild);

        // 自动关闭
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 300);
        }, duration);
    }
}

// 格式化日期时间
function formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// 复制到剪贴板
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showNotification('已复制到剪贴板', 'success', 2000);
    } catch (err) {
        console.error('复制失败:', err);
        showNotification('复制失败', 'danger');
    }
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ===== 表单验证 =====

class FormValidator {
    constructor(formId) {
        this.form = document.getElementById(formId);
        if (!this.form) return;

        this.init();
    }

    init() {
        // 实时验证
        this.form.querySelectorAll('.form-control').forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
            input.addEventListener('input', debounce(() => this.validateField(input), 500));
        });

        // 表单提交
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    validateField(input) {
        const value = input.value.trim();
        const type = input.type;
        const required = input.hasAttribute('required');

        // 清除之前的状态
        input.classList.remove('is-valid', 'is-invalid');

        // 必填验证
        if (required && !value) {
            this.setInvalid(input, '此字段为必填项');
            return false;
        }

        // 类型验证
        if (value) {
            if (type === 'email' && !this.isValidEmail(value)) {
                this.setInvalid(input, '请输入有效的邮箱地址');
                return false;
            }

            if (type === 'url' && !this.isValidUrl(value)) {
                this.setInvalid(input, '请输入有效的网址');
                return false;
            }

            if (type === 'tel' && !this.isValidPhone(value)) {
                this.setInvalid(input, '请输入有效的电话号码');
                return false;
            }

            // 自定义验证规则
            if (input.dataset.validate) {
                const validator = this[input.dataset.validate];
                if (validator && !validator.call(this, value)) {
                    this.setInvalid(input, input.dataset.errorMessage || '输入格式不正确');
                    return false;
                }
            }
        }

        this.setValid(input);
        return true;
    }

    setValid(input) {
        input.classList.add('is-valid');
        input.classList.remove('is-invalid');

        const feedback = input.parentElement.querySelector('.valid-feedback');
        if (feedback) {
            feedback.style.display = 'block';
        }

        const invalidFeedback = input.parentElement.querySelector('.invalid-feedback');
        if (invalidFeedback) {
            invalidFeedback.style.display = 'none';
        }
    }

    setInvalid(input, message) {
        input.classList.add('is-invalid');
        input.classList.remove('is-valid');

        let feedback = input.parentElement.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            input.parentElement.appendChild(feedback);
        }
        feedback.textContent = message;
        feedback.style.display = 'block';

        const validFeedback = input.parentElement.querySelector('.valid-feedback');
        if (validFeedback) {
            validFeedback.style.display = 'none';
        }
    }

    isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    isValidUrl(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }

    isValidPhone(phone) {
        return /^1[3-9]\d{9}$/.test(phone);
    }

    validateProductId(value) {
        return value.length >= 3 && /^[A-Za-z0-9_-]+$/.test(value);
    }

    validateBatchNumber(value) {
        return value.length >= 3;
    }

    validateDate(value) {
        const date = new Date(value);
        return !isNaN(date.getTime()) && date <= new Date();
    }

    handleSubmit(e) {
        e.preventDefault();

        // 验证所有字段
        let isValid = true;
        this.form.querySelectorAll('.form-control').forEach(input => {
            if (!this.validateField(input)) {
                isValid = false;
            }
        });

        if (!isValid) {
            showNotification('请修正表单中的错误', 'danger');
            // 聚焦到第一个错误字段
            const firstInvalid = this.form.querySelector('.is-invalid');
            if (firstInvalid) {
                firstInvalid.focus();
            }
            return;
        }

        // 显示加载状态
        const submitBtn = this.form.querySelector('button[type="submit"]');
        showLoading(submitBtn);

        // 提交表单
        this.form.submit();
    }
}

// ===== 图表管理 =====

class ChartManager {
    constructor() {
        this.charts = {};
    }

    // 创建统计图表
    createStatsChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }

        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: data.label || '数据',
                    data: data.values,
                    borderColor: CONFIG.chartColors.primary,
                    backgroundColor: CONFIG.chartColors.primary + '20',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });

        return this.charts[canvasId];
    }

    // 创建饼图
    createPieChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }

        this.charts[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.values,
                    backgroundColor: [
                        CONFIG.chartColors.primary,
                        CONFIG.chartColors.secondary,
                        CONFIG.chartColors.success,
                        CONFIG.chartColors.warning,
                        CONFIG.chartColors.danger,
                        CONFIG.chartColors.info
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });

        return this.charts[canvasId];
    }

    // 更新图表数据
    updateChart(canvasId, newData) {
        const chart = this.charts[canvasId];
        if (!chart) return;

        chart.data.labels = newData.labels;
        chart.data.datasets[0].data = newData.values;
        chart.update('none'); // 无动画更新
    }

    // 销毁图表
    destroyChart(canvasId) {
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
            delete this.charts[canvasId];
        }
    }
}

// ===== 实时数据更新 =====

class DataRefresher {
    constructor() {
        this.intervals = {};
    }

    // 开始自动刷新
    start(key, url, callback, interval = CONFIG.refreshInterval) {
        this.stop(key); // 先停止之前的

        const refresh = async () => {
            try {
                const response = await fetch(url);
                const data = await response.json();
                callback(data);
            } catch (error) {
                console.error('数据刷新失败:', error);
            }
        };

        // 立即执行一次
        refresh();

        // 设置定时刷新
        this.intervals[key] = setInterval(refresh, interval);
    }

    // 停止自动刷新
    stop(key) {
        if (this.intervals[key]) {
            clearInterval(this.intervals[key]);
            delete this.intervals[key];
        }
    }

    // 停止所有刷新
    stopAll() {
        Object.keys(this.intervals).forEach(key => this.stop(key));
    }
}

// ===== 数字动画 =====

function animateNumber(element, start, end, duration = 1000) {
    if (!element) return;

    const startTime = performance.now();
    const range = end - start;

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // 使用缓动函数
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        const current = Math.floor(start + range * easeOutQuart);

        element.textContent = current.toLocaleString();

        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            element.textContent = end.toLocaleString();
        }
    }

    requestAnimationFrame(update);
}

// ===== 表格增强 =====

class TableEnhancer {
    constructor(tableId) {
        this.table = document.getElementById(tableId);
        if (!this.table) return;

        this.init();
    }

    init() {
        // 添加搜索功能
        this.addSearch();

        // 添加排序功能
        this.addSort();

        // 添加行高亮
        this.addRowHighlight();
    }

    addSearch() {
        const searchInput = document.createElement('input');
        searchInput.type = 'text';
        searchInput.className = 'form-control mb-3';
        searchInput.placeholder = '搜索...';

        this.table.parentElement.insertBefore(searchInput, this.table);

        searchInput.addEventListener('input', debounce((e) => {
            const term = e.target.value.toLowerCase();
            const rows = this.table.querySelectorAll('tbody tr');

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(term) ? '' : 'none';
            });
        }, 300));
    }

    addSort() {
        const headers = this.table.querySelectorAll('thead th');

        headers.forEach((header, index) => {
            header.style.cursor = 'pointer';
            header.innerHTML += ' <i class="fas fa-sort ms-1"></i>';

            header.addEventListener('click', () => {
                this.sortTable(index);
            });
        });
    }

    sortTable(columnIndex) {
        const tbody = this.table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));

        rows.sort((a, b) => {
            const aValue = a.cells[columnIndex].textContent.trim();
            const bValue = b.cells[columnIndex].textContent.trim();

            // 尝试作为数字比较
            const aNum = parseFloat(aValue);
            const bNum = parseFloat(bValue);

            if (!isNaN(aNum) && !isNaN(bNum)) {
                return aNum - bNum;
            }

            // 字符串比较
            return aValue.localeCompare(bValue);
        });

        // 重新添加排序后的行
        rows.forEach(row => tbody.appendChild(row));
    }

    addRowHighlight() {
        const rows = this.table.querySelectorAll('tbody tr');

        rows.forEach(row => {
            row.addEventListener('click', () => {
                rows.forEach(r => r.classList.remove('table-active'));
                row.classList.add('table-active');
            });
        });
    }
}

// ===== 哈希值显示增强 =====

function enhanceHashDisplay() {
    document.querySelectorAll('code, .hash-text').forEach(element => {
        if (element.textContent.length > 20) {
            element.style.cursor = 'pointer';
            element.title = '点击复制';

            element.addEventListener('click', () => {
                copyToClipboard(element.textContent.trim());
            });
        }
    });
}

// ===== 页面特定功能 =====

// 仪表板初始化
function initDashboard() {
    // 数字动画
    document.querySelectorAll('.stat-number').forEach(element => {
        const target = parseInt(element.textContent);
        if (!isNaN(target)) {
            element.textContent = '0';
            setTimeout(() => animateNumber(element, 0, target), 300);
        }
    });

    // 创建图表（如果有Chart.js）
    if (typeof Chart !== 'undefined') {
        const chartManager = new ChartManager();

        // 示例：产品统计图表
        if (document.getElementById('productsChart')) {
            chartManager.createStatsChart('productsChart', {
                labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
                values: [12, 19, 15, 25, 22, 30],
                label: '产品数量'
            });
        }
    }

    // 自动刷新数据
    const dataRefresher = new DataRefresher();
    const currentPath = window.location.pathname;

    if (currentPath.includes('dashboard')) {
        // dataRefresher.start('dashboard', '/api/dashboard/stats', updateDashboardStats);
    }
}

// 区块链浏览器初始化
function initBlockchainExplorer() {
    // 添加区块展开/折叠功能
    document.querySelectorAll('.card-header').forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', () => {
            const body = header.nextElementSibling;
            if (body && body.classList.contains('card-body')) {
                body.style.display = body.style.display === 'none' ? 'block' : 'none';
            }
        });
    });

    // 哈希值复制功能
    enhanceHashDisplay();
}

// 产品追溯初始化
function initProductTrace() {
    // 时间轴动画
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.timeline-item').forEach(item => {
        observer.observe(item);
    });

    // 哈希值增强
    enhanceHashDisplay();
}

// ===== 页面加载完成后初始化 =====

document.addEventListener('DOMContentLoaded', () => {
    console.log('区块链溯源系统已加载 - 增强版');

    // 通用功能
    enhanceHashDisplay();

    // 初始化表单验证
    ['productRegistrationForm', 'qualityCheckForm', 'transferForm', 'logisticsForm'].forEach(formId => {
        if (document.getElementById(formId)) {
            new FormValidator(formId);
        }
    });

    // 根据页面类型初始化特定功能
    const path = window.location.pathname;

    if (path.includes('dashboard')) {
        initDashboard();
    } else if (path.includes('blockchain_explorer')) {
        initBlockchainExplorer();
    } else if (path.includes('trace')) {
        initProductTrace();
    }

    // 自动关闭警告框
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });

    // 平滑滚动
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // 按钮波纹效果
    document.querySelectorAll('.btn').forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.style.position = 'absolute';
            ripple.style.borderRadius = '50%';
            ripple.style.background = 'rgba(255, 255, 255, 0.6)';
            ripple.style.transform = 'scale(0)';
            ripple.style.animation = 'ripple 0.6s ease-out';
            ripple.style.pointerEvents = 'none';

            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);

            setTimeout(() => ripple.remove(), 600);
        });
    });
});

// 添加波纹动画CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// ===== 页面卸载时清理 =====
window.addEventListener('beforeunload', () => {
    if (AppState.dataRefresher) {
        AppState.dataRefresher.stopAll();
    }
});

// ===== 导出全局 API =====
window.BlockchainApp = {
    showLoading,
    hideLoading,
    showNotification,
    copyToClipboard,
    formatDateTime,
    FormValidator,
    ChartManager,
    DataRefresher,
    animateNumber,
    TableEnhancer
};
