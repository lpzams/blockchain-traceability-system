// ===== 消费者角色专属 JavaScript =====

// ===== 收藏功能 =====
async function toggleFavorite(productId) {
    const productIdToUse = productId || document.querySelector('[data-product-id]')?.dataset.productId;
    if (!productIdToUse) {
        console.error('Product ID not found');
        return;
    }

    const favoriteBtn = document.getElementById('favoriteBtn');
    const favoriteText = document.getElementById('favoriteText');
    const isFavorited = favoriteText && favoriteText.textContent === '已收藏';

    try {
        const response = isFavorited
            ? await fetch(`/consumer/api/favorite/${productIdToUse}`, { method: 'DELETE' })
            : await fetch(`/consumer/api/favorite/${productIdToUse}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

        const data = await response.json();

        if (data.success) {
            if (isFavorited) {
                if (favoriteText) favoriteText.textContent = '收藏';
                if (favoriteBtn) favoriteBtn.classList.remove('favorited');
                if (window.BlockchainApp && window.BlockchainApp.showNotification) {
                    window.BlockchainApp.showNotification('已取消收藏', 'info');
                }
            } else {
                if (favoriteText) favoriteText.textContent = '已收藏';
                if (favoriteBtn) favoriteBtn.classList.add('favorited');
                if (window.BlockchainApp && window.BlockchainApp.showNotification) {
                    window.BlockchainApp.showNotification('收藏成功', 'success');
                }
            }
        } else {
            if (window.BlockchainApp && window.BlockchainApp.showNotification) {
                window.BlockchainApp.showNotification(data.error || '操作失败', 'danger');
            }
        }
    } catch (error) {
        console.error('Error:', error);
        if (window.BlockchainApp && window.BlockchainApp.showNotification) {
            window.BlockchainApp.showNotification('操作失败', 'danger');
        }
    }
}

// ===== 关注功能 =====
async function toggleWatch(productId, notifyOnTransfer = true, notifyOnQualityCheck = true) {
    const productIdToUse = productId || document.querySelector('[data-product-id]')?.dataset.productId;
    if (!productIdToUse) {
        console.error('Product ID not found');
        return;
    }

    const watchBtn = document.getElementById('watchBtn');
    const watchText = document.getElementById('watchText');
    const isWatched = watchText && watchText.textContent === '已关注';

    try {
        const response = isWatched
            ? await fetch(`/consumer/api/watch/${productIdToUse}`, { method: 'DELETE' })
            : await fetch(`/consumer/api/watch/${productIdToUse}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    notify_on_transfer: notifyOnTransfer,
                    notify_on_quality_check: notifyOnQualityCheck
                })
            });

        const data = await response.json();

        if (data.success) {
            if (isWatched) {
                if (watchText) watchText.textContent = '关注';
                if (watchBtn) watchBtn.classList.remove('watched');
                if (window.BlockchainApp && window.BlockchainApp.showNotification) {
                    window.BlockchainApp.showNotification('已取消关注', 'info');
                }
            } else {
                if (watchText) watchText.textContent = '已关注';
                if (watchBtn) watchBtn.classList.add('watched');
                if (window.BlockchainApp && window.BlockchainApp.showNotification) {
                    window.BlockchainApp.showNotification('关注成功', 'success');
                }
            }
        } else {
            if (window.BlockchainApp && window.BlockchainApp.showNotification) {
                window.BlockchainApp.showNotification(data.error || '操作失败', 'danger');
            }
        }
    } catch (error) {
        console.error('Error:', error);
        if (window.BlockchainApp && window.BlockchainApp.showNotification) {
            window.BlockchainApp.showNotification('操作失败', 'danger');
        }
    }
}

// ===== 产品评价 =====
async function submitRating(productId, rating, comment) {
    if (!productId || !rating) {
        if (window.BlockchainApp && window.BlockchainApp.showNotification) {
            window.BlockchainApp.showNotification('请填写评分', 'warning');
        }
        return;
    }

    try {
        const response = await fetch(`/consumer/api/rate/${productId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                rating: parseInt(rating),
                comment: comment || ''
            })
        });

        const data = await response.json();

        if (data.success) {
            if (window.BlockchainApp && window.BlockchainApp.showNotification) {
                window.BlockchainApp.showNotification('评价提交成功', 'success');
            }
            setTimeout(() => location.reload(), 1500);
        } else {
            if (window.BlockchainApp && window.BlockchainApp.showNotification) {
                window.BlockchainApp.showNotification(data.error || '评价提交失败', 'danger');
            }
        }
    } catch (error) {
        console.error('Error:', error);
        if (window.BlockchainApp && window.BlockchainApp.showNotification) {
            window.BlockchainApp.showNotification('评价提交失败', 'danger');
        }
    }
}

// ===== 产品对比 =====
async function compareProducts(productIds) {
    if (!productIds || productIds.length < 2) {
        if (window.BlockchainApp && window.BlockchainApp.showNotification) {
            window.BlockchainApp.showNotification('请至少选择2个产品进行对比', 'warning');
        }
        return;
    }

    try {
        const response = await fetch('/consumer/api/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_ids: productIds
            })
        });

        const data = await response.json();

        if (data.success) {
            const url = new URL('/consumer/compare', window.location.origin);
            productIds.forEach(id => url.searchParams.append('products', id));
            window.location.href = url.toString();
        } else {
            if (window.BlockchainApp && window.BlockchainApp.showNotification) {
                window.BlockchainApp.showNotification(data.error || '对比失败', 'danger');
            }
        }
    } catch (error) {
        console.error('Error:', error);
        if (window.BlockchainApp && window.BlockchainApp.showNotification) {
            window.BlockchainApp.showNotification('对比失败', 'danger');
        }
    }
}

// ===== 二维码生成 =====
async function generateQRCode(productId) {
    if (!productId) {
        if (window.BlockchainApp && window.BlockchainApp.showNotification) {
            window.BlockchainApp.showNotification('产品ID不存在', 'warning');
        }
        return;
    }

    try {
        const btn = document.querySelector('[data-action="generate-qr"]');
        if (btn && window.BlockchainApp && window.BlockchainApp.showLoading) {
            window.BlockchainApp.showLoading(btn);
        }

        const response = await fetch(`/consumer/api/qrcode/${productId}`);
        const data = await response.json();

        if (data.success) {
            const qrContainer = document.getElementById('qrcodeContainer');
            if (qrContainer) {
                qrContainer.innerHTML = `<img src="data:image/png;base64,${data.qr_code}" alt="QR Code">`;
            }
            if (window.BlockchainApp && window.BlockchainApp.showNotification) {
                window.BlockchainApp.showNotification('二维码已生成', 'success');
            }
        } else {
            if (window.BlockchainApp && window.BlockchainApp.showNotification) {
                window.BlockchainApp.showNotification(data.error || '二维码生成失败', 'danger');
            }
        }
    } catch (error) {
        console.error('Error:', error);
        if (window.BlockchainApp && window.BlockchainApp.showNotification) {
            window.BlockchainApp.showNotification('二维码生成失败', 'danger');
        }
    }
}

// ===== 搜索功能增强 =====
class ConsumerSearchEnhancer {
    constructor() {
        this.init();
    }

    init() {
        const searchForm = document.querySelector('.search-form');
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => this.handleSearch(e));
        }

        this.addSearchSuggestions();
    }

    async handleSearch(e) {
        // 可选：添加自定义搜索逻辑
    }

    addSearchSuggestions() {
        const keywordInput = document.getElementById('keyword');
        if (!keywordInput) return;

        keywordInput.addEventListener('input', (e) => {
            const keyword = e.target.value;
            if (keyword.length > 1) {
                this.fetchSuggestions(keyword);
            }
        });
    }

    async fetchSuggestions(keyword) {
        // 可选：从API获取搜索建议
    }
}

// ===== 我的收藏/关注管理 =====
class FavoriteManager {
    constructor() {
        this.init();
    }

    init() {
        const removeButtons = document.querySelectorAll('[data-action="remove-favorite"]');
        removeButtons.forEach(btn => {
            btn.addEventListener('click', (e) => this.removeFavorite(e));
        });
    }

    async removeFavorite(e) {
        const productId = e.target.dataset.productId;
        if (!productId) return;

        if (confirm('确定要取消收藏吗？')) {
            try {
                const response = await fetch(`/consumer/api/favorite/${productId}`, {
                    method: 'DELETE'
                });

                const data = await response.json();
                if (data.success) {
                    if (window.BlockchainApp && window.BlockchainApp.showNotification) {
                        window.BlockchainApp.showNotification('已取消收藏', 'success');
                    }
                    e.target.closest('.list-item').remove();
                } else {
                    if (window.BlockchainApp && window.BlockchainApp.showNotification) {
                        window.BlockchainApp.showNotification(data.error || '操作失败', 'danger');
                    }
                }
            } catch (error) {
                if (window.BlockchainApp && window.BlockchainApp.showNotification) {
                    window.BlockchainApp.showNotification('操作失败', 'danger');
                }
            }
        }
    }
}

// ===== 页面初始化 =====
document.addEventListener('DOMContentLoaded', () => {
    console.log('Consumer script loaded');

    if (window.location.pathname.includes('/consumer/search')) {
        new ConsumerSearchEnhancer();
    }

    if (window.location.pathname.includes('/consumer/favorites')) {
        new FavoriteManager();
    }

    const favoriteBtn = document.getElementById('favoriteBtn');
    if (favoriteBtn) {
        const productId = document.querySelector('[data-product-id]')?.dataset.productId;
        if (productId) {
            fetch(`/consumer/api/favorite/${productId}/status`)
                .then(r => r.json())
                .then(data => {
                    if (data.success && data.is_favorited) {
                        const favoriteText = document.getElementById('favoriteText');
                        if (favoriteText) favoriteText.textContent = '已收藏';
                        favoriteBtn.classList.add('favorited');
                    }
                })
                .catch(err => console.error('Error checking favorite status:', err));
        }
    }

    const watchBtn = document.getElementById('watchBtn');
    if (watchBtn) {
        const productId = document.querySelector('[data-product-id]')?.dataset.productId;
        if (productId) {
            fetch(`/consumer/api/watch/${productId}/status`)
                .then(r => r.json())
                .then(data => {
                    if (data.success && data.is_watched) {
                        const watchText = document.getElementById('watchText');
                        if (watchText) watchText.textContent = '已关注';
                        watchBtn.classList.add('watched');
                    }
                })
                .catch(err => console.error('Error checking watch status:', err));
        }
    }

    window.ConsumerApp = {
        toggleFavorite,
        toggleWatch,
        submitRating,
        compareProducts,
        generateQRCode,
        FavoriteManager,
        ConsumerSearchEnhancer
    };
});
