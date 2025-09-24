// E-commerce Search Application JavaScript

class EcommerceSearch {
    constructor() {
        this.weights = {
            description_semantic_elser: 2,
            description_semantic_google: 2.5,
            description_semantic_e5: 2,
            product_name_semantic_elser: 2,
            product_name_semantic_google: 2.5,
            product_name_semantic_e5: 2,
            multi_match: 2,
            model_number: 1.0,
            product_id: 2.9
        };
        this.enabledFields = {
            description_semantic_elser: false,
            description_semantic_google: true,
            description_semantic_e5: false,
            product_name_semantic_elser: false,
            product_name_semantic_google: true,
            product_name_semantic_e5: false,
            multi_match: false,
            model_number: true,
            product_id: true
        };
        this.multiMatchFields = ['description', 'product_name'];
        this.enableReranking = false;
        this.rerankField = 'description';
        this.queryUpdateTimeout = null;
        this.currentQuery = '';
        
        this.initializeEventListeners();
        this.loadInitialData();
    }
    
    initializeEventListeners() {
        // Search button
        document.getElementById('searchBtn').addEventListener('click', () => {
            this.performSearch();
        });
        
        // Enter key in search input
        document.getElementById('searchQuery').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });
        
        // Weight slider changes with debouncing
        document.querySelectorAll('.weight-slider').forEach(slider => {
            slider.addEventListener('input', (e) => {
                this.handleWeightChange(e.target);
            });
        });
        
        // Field enable/disable checkboxes
        document.querySelectorAll('.field-enable-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                this.handleFieldEnableChange(e.target);
            });
        });
        
        // Multi-match field checkboxes
        document.querySelectorAll('.multi-match-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateMultiMatchFields();
                this.scheduleQueryUpdate();
            });
        });
        
        // Reranking checkbox
        document.getElementById('enableReranking').addEventListener('change', (e) => {
            this.enableReranking = e.target.checked;
            this.toggleRerankFieldSelection();
            this.scheduleQueryUpdate();
        });
        
        // Reranking field dropdown
        document.getElementById('rerankField').addEventListener('change', (e) => {
            this.rerankField = e.target.value;
            this.scheduleQueryUpdate();
        });
        
        // Show query button
        document.getElementById('showQueryBtn').addEventListener('click', () => {
            this.showGeneratedQuery();
        });
        
        // Reset weights button
        document.getElementById('resetWeightsBtn').addEventListener('click', () => {
            this.resetAllWeights();
        });
        
        // Copy query button
        document.getElementById('copyQueryBtn').addEventListener('click', () => {
            this.copyQuery();
        });
        
        // Product card clicks (using event delegation)
        document.getElementById('resultsGrid').addEventListener('click', (e) => {
            const productCard = e.target.closest('.product-card');
            if (productCard) {
                const productData = JSON.parse(productCard.dataset.product);
                this.showProductDetail(productData);
            }
        });
        
        // Recommendation card clicks (using event delegation)
        document.addEventListener('click', (e) => {
            const recommendationCard = e.target.closest('.recommendation-card');
            if (recommendationCard) {
                const productData = JSON.parse(recommendationCard.dataset.product);
                this.showProductDetail(productData);
            }
        });
    }
    
    loadInitialData() {
        // Initialize visual state of field checkboxes and sliders
        this.initializeFieldStates();
        
        // Load some initial products on page load
        this.performSearch();
    }
    
    initializeFieldStates() {
        // Set the visual state of all fields based on enabledFields
        document.querySelectorAll('.field-enable-checkbox').forEach(checkbox => {
            const field = checkbox.dataset.field;
            const isEnabled = this.enabledFields[field];
            
            // Set checkbox state
            checkbox.checked = isEnabled;
            
            // Set visual state of slider and container
            const weightItem = checkbox.closest('.weight-item');
            const slider = weightItem.querySelector('.weight-slider');
            const valueDisplay = weightItem.querySelector('.slider-value');
            
            if (isEnabled) {
                slider.disabled = false;
                slider.classList.remove('disabled');
                weightItem.classList.remove('disabled');
                if (valueDisplay) {
                    valueDisplay.classList.remove('disabled');
                }
            } else {
                slider.disabled = true;
                slider.classList.add('disabled');
                weightItem.classList.add('disabled');
                if (valueDisplay) {
                    valueDisplay.classList.add('disabled');
                }
            }
        });
    }
    
    handleWeightChange(slider) {
        const field = slider.dataset.field;
        const value = parseFloat(slider.value) || 0;
        
        // Update weights object
        this.weights[field] = value;
        
        // Update the value display
        const valueDisplay = slider.parentElement.querySelector('.slider-value');
        if (valueDisplay) {
            valueDisplay.textContent = value.toFixed(1);
        }
        
        // Visual feedback
        slider.classList.add('changed');
        if (valueDisplay) {
            valueDisplay.classList.add('changed');
        }
        setTimeout(() => {
            slider.classList.remove('changed');
            if (valueDisplay) {
                valueDisplay.classList.remove('changed');
            }
        }, 500);
        
        // Schedule query update with 2-second delay
        this.scheduleQueryUpdate();
    }
    
    handleFieldEnableChange(checkbox) {
        const field = checkbox.dataset.field;
        const isEnabled = checkbox.checked;
        
        // Update enabled fields object
        this.enabledFields[field] = isEnabled;
        
        // Update visual state of the slider
        const weightItem = checkbox.closest('.weight-item');
        const slider = weightItem.querySelector('.weight-slider');
        const valueDisplay = weightItem.querySelector('.slider-value');
        
        if (isEnabled) {
            slider.disabled = false;
            slider.classList.remove('disabled');
            weightItem.classList.remove('disabled');
            if (valueDisplay) {
                valueDisplay.classList.remove('disabled');
            }
        } else {
            slider.disabled = true;
            slider.classList.add('disabled');
            weightItem.classList.add('disabled');
            if (valueDisplay) {
                valueDisplay.classList.add('disabled');
            }
        }
        
        // Schedule query update with 2-second delay
        this.scheduleQueryUpdate();
    }
    
    updateMultiMatchFields() {
        this.multiMatchFields = Array.from(document.querySelectorAll('.multi-match-checkbox:checked'))
            .map(checkbox => checkbox.value);
    }
    
    getEnabledWeights() {
        const enabledWeights = {};
        for (const [field, weight] of Object.entries(this.weights)) {
            if (this.enabledFields[field]) {
                enabledWeights[field] = weight;
            }
        }
        return enabledWeights;
    }
    
    toggleRerankFieldSelection() {
        const rerankFieldSelection = document.getElementById('rerankFieldSelection');
        if (this.enableReranking) {
            rerankFieldSelection.style.display = 'block';
        } else {
            rerankFieldSelection.style.display = 'none';
        }
    }
    
    resetAllWeights() {
        // Reset all weights to 0
        Object.keys(this.weights).forEach(field => {
            this.weights[field] = 0;
        });
        
        // Update all sliders to 0
        document.querySelectorAll('.weight-slider').forEach(slider => {
            slider.value = 0;
            const valueDisplay = slider.parentElement.querySelector('.slider-value');
            if (valueDisplay) {
                valueDisplay.textContent = '0.0';
            }
            
            // Add visual feedback
            slider.classList.add('changed');
            if (valueDisplay) {
                valueDisplay.classList.add('changed');
            }
            setTimeout(() => {
                slider.classList.remove('changed');
                if (valueDisplay) {
                    valueDisplay.classList.remove('changed');
                }
            }, 500);
        });
        
        // Schedule query update
        this.scheduleQueryUpdate();
    }
    
    scheduleQueryUpdate() {
        // Clear existing timeout
        if (this.queryUpdateTimeout) {
            clearTimeout(this.queryUpdateTimeout);
        }
        
        // Set new timeout for 2 seconds
        this.queryUpdateTimeout = setTimeout(() => {
            this.updateGeneratedQuery();
        }, 2000);
    }
    
    async updateGeneratedQuery() {
        const query = document.getElementById('searchQuery').value;
        if (!query.trim()) return;
        
        try {
            const response = await fetch('/generate_query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    weights: this.getEnabledWeights(),
                    multi_match_fields: this.multiMatchFields,
                    enable_reranking: this.enableReranking,
                    rerank_field: this.rerankField
                })
            });
            
            const data = await response.json();
            if (data.success) {
                this.currentQuery = data.query;
            }
        } catch (error) {
            console.error('Error updating query:', error);
        }
    }
    
    async performSearch() {
        const query = document.getElementById('searchQuery').value;
        if (!query.trim()) {
            this.showNoResults('Please enter a search query');
            return;
        }
        
        this.showLoading();
        
        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    weights: this.getEnabledWeights(),
                    multi_match_fields: this.multiMatchFields,
                    enable_reranking: this.enableReranking,
                    rerank_field: this.rerankField
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentQuery = data.query;
                this.displayResults(data.products, data.total);
            } else {
                this.showError(data.error || 'Search failed');
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        }
    }
    
    displayResults(products, total) {
        this.hideLoading();
        
        const resultsGrid = document.getElementById('resultsGrid');
        const searchStats = document.getElementById('searchStats');
        const resultCount = document.getElementById('resultCount');
        const noResults = document.getElementById('noResults');
        
        // Update stats
        resultCount.textContent = `${total} result${total !== 1 ? 's' : ''}`;
        searchStats.style.display = 'flex';
        
        if (products.length === 0) {
            resultsGrid.innerHTML = '';
            noResults.style.display = 'block';
            return;
        }
        
        noResults.style.display = 'none';
        
        // Generate product cards
        resultsGrid.innerHTML = products.map(product => this.createProductCard(product)).join('');
    }
    
    createProductCard(product) {
        const imageHtml = product.main_image 
            ? `<img src="${product.main_image}" alt="${product.product_name}" class="product-image" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">`
            : '';
        
        const placeholderHtml = `<div class="product-image-placeholder" style="display: ${product.main_image ? 'none' : 'flex'};">
            <i class="fas fa-image"></i>
        </div>`;
        
        const priceHtml = product.final_price 
            ? `<div class="product-price">${product.currency} ${product.final_price.toFixed(2)}</div>`
            : '';
        
        const ratingHtml = product.rating 
            ? `<div class="product-rating">
                <span class="rating-stars">${'★'.repeat(Math.floor(product.rating))}${'☆'.repeat(5 - Math.floor(product.rating))}</span>
                <span class="rating-text">${product.rating.toFixed(1)} (${product.reviews_count} reviews)</span>
            </div>`
            : '';
        
        const stockHtml = `<div class="product-stock">
            <span class="stock-badge ${product.in_stock ? 'stock-in' : 'stock-out'}">
                ${product.in_stock ? 'In Stock' : 'Out of Stock'}
            </span>
        </div>`;
        
        return `
            <div class="col-lg-4 col-md-6 mb-4">
                <div class="product-card" data-product='${JSON.stringify(product)}' style="cursor: pointer;">
                    ${imageHtml}
                    ${placeholderHtml}
                    <div class="product-info">
                        <h5 class="product-name">${product.product_name || 'No name available'}</h5>
                        <p class="product-description">${product.description || 'No description available'}</p>
                        ${priceHtml}
                        ${ratingHtml}
                        ${stockHtml}
                    </div>
                </div>
            </div>
        `;
    }
    
    showLoading() {
        document.getElementById('loadingSpinner').style.display = 'block';
        document.getElementById('resultsGrid').innerHTML = '';
        document.getElementById('noResults').style.display = 'none';
        document.getElementById('searchStats').style.display = 'none';
    }
    
    hideLoading() {
        document.getElementById('loadingSpinner').style.display = 'none';
    }
    
    showNoResults(message) {
        this.hideLoading();
        document.getElementById('resultsGrid').innerHTML = '';
        document.getElementById('noResults').style.display = 'block';
        document.getElementById('searchStats').style.display = 'none';
        
        const noResultsDiv = document.getElementById('noResults');
        noResultsDiv.querySelector('h4').textContent = message || 'No products found';
    }
    
    showError(errorMessage) {
        this.hideLoading();
        this.showNoResults('Error: ' + errorMessage);
    }
    
    async showGeneratedQuery() {
        if (!this.currentQuery) {
            // Generate query if not available
            const query = document.getElementById('searchQuery').value;
            if (!query.trim()) {
                alert('Please enter a search query first');
                return;
            }
            
            try {
                const response = await fetch('/generate_query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        query: query,
                        weights: this.getEnabledWeights(),
                        multi_match_fields: this.multiMatchFields,
                        enable_reranking: this.enableReranking,
                        rerank_field: this.rerankField
                    })
                });
                
                const data = await response.json();
                if (data.success) {
                    this.currentQuery = data.query;
                } else {
                    alert('Error generating query: ' + data.error);
                    return;
                }
            } catch (error) {
                alert('Error generating query: ' + error.message);
                return;
            }
        }
        
        // Show the query in modal
        document.getElementById('queryContent').textContent = JSON.stringify(this.currentQuery, null, 2);
        const modal = new bootstrap.Modal(document.getElementById('queryModal'));
        modal.show();
    }
    
    copyQuery() {
        const queryContent = document.getElementById('queryContent').textContent;
        navigator.clipboard.writeText(queryContent).then(() => {
            // Show success feedback
            const copyBtn = document.getElementById('copyQueryBtn');
            const originalText = copyBtn.textContent;
            copyBtn.textContent = 'Copied!';
            copyBtn.classList.remove('btn-primary');
            copyBtn.classList.add('btn-success');
            
            setTimeout(() => {
                copyBtn.textContent = originalText;
                copyBtn.classList.remove('btn-success');
                copyBtn.classList.add('btn-primary');
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy query: ', err);
            alert('Failed to copy query to clipboard');
        });
    }
    
    async showProductDetail(product) {
        console.log('DEBUG: Product object in showProductDetail:', product);
        console.log('DEBUG: product.product_id:', product.product_id);
        console.log('DEBUG: product.id:', product.id);
        
        // Populate modal with product data
        document.getElementById('productDetailTitle').textContent = product.product_name || 'Product Details';
        document.getElementById('productDetailName').textContent = product.product_name || 'No name available';
        document.getElementById('productDetailId').textContent = product.product_id || 'N/A';
        document.getElementById('productDetailModelNumber').textContent = product.model_number || 'N/A';
        document.getElementById('productDetailScore').textContent = product.score ? product.score.toFixed(2) : 'N/A';
        
        // Handle product image
        const productImage = document.getElementById('productDetailImage');
        const imagePlaceholder = document.getElementById('productDetailImagePlaceholder');
        
        if (product.main_image) {
            productImage.src = product.main_image;
            productImage.style.display = 'block';
            imagePlaceholder.style.display = 'none';
            productImage.onerror = () => {
                productImage.style.display = 'none';
                imagePlaceholder.style.display = 'flex';
            };
        } else {
            productImage.style.display = 'none';
            imagePlaceholder.style.display = 'flex';
        }
        
        // Handle price
        const priceElement = document.getElementById('productDetailPrice');
        if (product.final_price) {
            priceElement.innerHTML = `<strong>${product.currency} ${product.final_price.toFixed(2)}</strong>`;
            priceElement.style.display = 'block';
        } else {
            priceElement.style.display = 'none';
        }
        
        // Handle rating
        const ratingElement = document.getElementById('productDetailRating');
        if (product.rating) {
            const stars = '★'.repeat(Math.floor(product.rating)) + '☆'.repeat(5 - Math.floor(product.rating));
            ratingElement.innerHTML = `
                <span class="rating-stars">${stars}</span>
                <span class="rating-text">${product.rating.toFixed(1)} (${product.reviews_count} reviews)</span>
            `;
            ratingElement.style.display = 'flex';
        } else {
            ratingElement.style.display = 'none';
        }
        
        // Handle stock status
        const stockElement = document.getElementById('productDetailStock');
        const stockBadge = product.in_stock ? 'In Stock' : 'Out of Stock';
        const stockClass = product.in_stock ? 'stock-in' : 'stock-out';
        stockElement.innerHTML = `<span class="stock-badge ${stockClass}">${stockBadge}</span>`;
        
        // Handle description
        const descriptionElement = document.getElementById('productDetailDescription');
        descriptionElement.textContent = product.description || 'No description available';
        
        // Show loading for recommendations
        this.showRecommendationsLoading();
        
        // Show the modal
        const modal = new bootstrap.Modal(document.getElementById('productDetailModal'));
        modal.show();
        
        // Fetch and display recommendations
        await this.loadRecommendations(product.product_id);
    }
    
    showRecommendationsLoading() {
        const recommendationsContainer = document.getElementById('recommendationsContainer');
        recommendationsContainer.innerHTML = `
            <div class="text-center py-3">
                <div class="spinner-border spinner-border-sm text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <span class="ms-2">Loading recommendations...</span>
            </div>
        `;
    }
    
    async loadRecommendations(productId) {
        try {
            console.log('DEBUG: Loading recommendations for productId:', productId);
            const response = await fetch('/recommendations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    product_id: productId
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayRecommendations(data.recommendations);
            } else {
                this.showRecommendationsError(data.error || 'Failed to load recommendations');
            }
        } catch (error) {
            this.showRecommendationsError('Network error: ' + error.message);
        }
    }
    
    displayRecommendations(recommendations) {
        const recommendationsContainer = document.getElementById('recommendationsContainer');
        
        if (!recommendations || recommendations.length === 0) {
            recommendationsContainer.innerHTML = `
                <div class="text-center py-3 text-muted">
                    <i class="fas fa-info-circle"></i>
                    <span class="ms-2">No recommendations available for this product</span>
                </div>
            `;
            return;
        }
        
        const recommendationsHtml = recommendations.map(product => this.createRecommendationCard(product)).join('');
        
        recommendationsContainer.innerHTML = `
            <div class="recommendations-section">
                <h6 class="recommendations-title">
                    <i class="fas fa-thumbs-up"></i> Frequently Bought Together
                </h6>
                <div class="recommendations-grid">
                    ${recommendationsHtml}
                </div>
            </div>
        `;
    }
    
    createRecommendationCard(product) {
        const imageHtml = product.main_image 
            ? `<img src="${product.main_image}" alt="${product.product_name}" class="recommendation-image" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">`
            : '';
        
        const placeholderHtml = `<div class="recommendation-image-placeholder" style="display: ${product.main_image ? 'none' : 'flex'};">
            <i class="fas fa-image"></i>
        </div>`;
        
        const priceHtml = product.final_price 
            ? `<div class="recommendation-price">${product.currency} ${product.final_price.toFixed(2)}</div>`
            : '';
        
        const ratingHtml = product.rating 
            ? `<div class="recommendation-rating">
                <span class="rating-stars">${'★'.repeat(Math.floor(product.rating))}${'☆'.repeat(5 - Math.floor(product.rating))}</span>
                <span class="rating-text">${product.rating.toFixed(1)}</span>
            </div>`
            : '';
        
        return `
            <div class="recommendation-card" data-product='${JSON.stringify(product)}' style="cursor: pointer;">
                ${imageHtml}
                ${placeholderHtml}
                <div class="recommendation-info">
                    <h6 class="recommendation-name">${product.product_name || 'No name available'}</h6>
                    ${priceHtml}
                    ${ratingHtml}
                </div>
            </div>
        `;
    }
    
    showRecommendationsError(errorMessage) {
        const recommendationsContainer = document.getElementById('recommendationsContainer');
        recommendationsContainer.innerHTML = `
            <div class="text-center py-3 text-danger">
                <i class="fas fa-exclamation-triangle"></i>
                <span class="ms-2">Error loading recommendations: ${errorMessage}</span>
            </div>
        `;
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new EcommerceSearch();
});
