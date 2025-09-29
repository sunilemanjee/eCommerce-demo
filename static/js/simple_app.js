// Simple E-commerce Search Application JavaScript

class SimpleEcommerceSearch {
    constructor() {
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
    }
    
    loadInitialData() {
        // Load some initial products on page load
        this.performSearch();
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
                    query: query
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
        
        // Add highlights if available
        let highlightHtml = '';
        if (product.highlights && product.highlights.product_name) {
            highlightHtml = `<div class="product-highlights">
                <small class="text-muted">Highlights: ${product.highlights.product_name.join(' ... ')}</small>
            </div>`;
        }
        
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
                        ${highlightHtml}
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
    
    showProductDetail(product) {
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
        
        // Show the modal
        const modal = new bootstrap.Modal(document.getElementById('productDetailModal'));
        modal.show();
    }
    
    copyQuery() {
        if (!this.currentQuery) {
            alert('No query available to copy');
            return;
        }
        
        const queryContent = JSON.stringify(this.currentQuery, null, 2);
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
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SimpleEcommerceSearch();
});
