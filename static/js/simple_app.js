// Synonym E-commerce Search Application JavaScript

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
        
        // Reset synonyms button
        document.getElementById('resetSynonymsBtn').addEventListener('click', () => {
            this.resetSynonyms();
        });
        
        // Manage synonyms button
        document.getElementById('manageSynonymsBtn').addEventListener('click', () => {
            this.manageSynonyms();
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
        
        // Get the selected search type
        const searchType = document.querySelector('input[name="searchType"]:checked').value;
        
        this.showLoading();
        
        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    search_type: searchType
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
    
    async displayResults(products, total) {
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
            
            // Try to get search refinements for the current query
            const currentQuery = document.getElementById('searchQuery').value.toLowerCase().trim();
            if (currentQuery) {
                await this.showSearchRefinementSuggestion(currentQuery);
            }
            return;
        }
        
        noResults.style.display = 'none';
        
        // Hide suggestion when there are results
        const suggestionBox = noResults.querySelector('.suggestion-box');
        if (suggestionBox) {
            suggestionBox.style.display = 'none';
        }
        
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
        
        // Skip highlights display - not needed for synonyms UI
        
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
    
    showNoResults(message, showSuggestion = false) {
        this.hideLoading();
        document.getElementById('resultsGrid').innerHTML = '';
        document.getElementById('noResults').style.display = 'block';
        document.getElementById('searchStats').style.display = 'none';
        
        const noResultsDiv = document.getElementById('noResults');
        noResultsDiv.querySelector('h4').textContent = message || 'No products found';
        
        // Show/hide suggestion based on parameter
        const suggestionBox = noResultsDiv.querySelector('.suggestion-box');
        if (suggestionBox) {
            suggestionBox.style.display = showSuggestion ? 'inline-block' : 'none';
        }
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
    
    async showSearchRefinementSuggestion(query) {
        try {
            const response = await fetch(`/search-refinements/${encodeURIComponent(query)}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            const suggestionBox = document.querySelector('.suggestion-box');
            
            if (data.success && data.data && data.data.best_recommendation) {
                const recommendation = data.data.best_recommendation;
                const suggestionText = suggestionBox.querySelector('span');
                const suggestionButton = suggestionBox.querySelector('button');
                
                // Update the suggestion text and button
                suggestionText.textContent = `Try searching for `;
                suggestionButton.textContent = recommendation.term;
                suggestionButton.onclick = () => {
                    document.getElementById('searchQuery').value = recommendation.term;
                    document.getElementById('searchBtn').click();
                };
                
                // Show the suggestion box
                suggestionBox.style.display = 'inline-block';
            } else {
                // Hide suggestion box if no refinements found
                suggestionBox.style.display = 'none';
            }
        } catch (error) {
            console.error('Error fetching search refinements:', error);
            // Hide suggestion box on error
            const suggestionBox = document.querySelector('.suggestion-box');
            if (suggestionBox) {
                suggestionBox.style.display = 'none';
            }
        }
    }

    async resetSynonyms() {
        try {
            console.log('Resetting synonyms...');
            
            // Disable button and show loading state
            const resetBtn = document.getElementById('resetSynonymsBtn');
            const originalText = resetBtn.innerHTML;
            resetBtn.disabled = true;
            resetBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Resetting...';
            
            // Step 1: GET _synonyms/yeti to get the rule ID
            const getResponse = await fetch('/synonyms/yeti', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            // Check if response is JSON
            const contentType = getResponse.headers.get('content-type');
            console.log('Response content-type:', contentType);
            
            if (!contentType || !contentType.includes('application/json')) {
                const textResponse = await getResponse.text();
                console.log('Non-JSON response:', textResponse.substring(0, 200) + '...');
                throw new Error(`Server returned non-JSON response: ${contentType}`);
            }
            
            const getData = await getResponse.json();
            console.log('Synonyms API response:', getData);
            console.log('Response status:', getResponse.status);
            console.log('getData.success:', getData.success);
            console.log('getData.data:', getData.data);
            console.log('getData.data type:', typeof getData.data);
            console.log('getData.data keys:', getData.data ? Object.keys(getData.data) : 'N/A');
            
            if (getData.success && getData.data && getData.data.synonyms_set && getData.data.synonyms_set.length > 0) {
                const ruleId = getData.data.synonyms_set[0].id;
                console.log('Found rule ID:', ruleId);
                
                // Step 2: PUT _synonyms/yeti/{rule_id} with synonyms: "yeti"
                const putResponse = await fetch(`/synonyms/yeti/${ruleId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        synonyms: 'yeti'
                    })
                });
                
                const putData = await putResponse.json();
                
                if (putData.success) {
                    console.log('Synonyms reset successfully! Set to:', 'yeti');
                    // Show success message
                    this.showMessage('Synonyms reset successfully!', 'success');
                } else {
                    console.error('Error resetting synonyms:', putData.error);
                    this.showMessage('Error resetting synonyms: ' + putData.error, 'error');
                }
            } else {
                console.log('No synonyms found or error in GET request');
                console.log('Debug info:');
                console.log('- getData.success:', getData.success);
                console.log('- getData.data exists:', !!getData.data);
                console.log('- getData.data.synonyms_set exists:', !!(getData.data && getData.data.synonyms_set));
                console.log('- synonyms_set length:', getData.data && getData.data.synonyms_set ? getData.data.synonyms_set.length : 'N/A');
                
                let errorMsg = 'No synonyms found or error in GET request';
                if (!getData.success) {
                    errorMsg = 'API request failed: ' + (getData.error || 'Unknown error');
                } else if (!getData.data) {
                    errorMsg = 'No data returned from API';
                } else if (!getData.data.synonyms_set) {
                    errorMsg = 'No synonyms_set in response data';
                } else if (getData.data.synonyms_set.length === 0) {
                    errorMsg = 'Synonyms set is empty';
                }
                
                this.showMessage(errorMsg, 'error');
            }
        } catch (error) {
            console.error('Error resetting synonyms:', error);
            this.showMessage('Error resetting synonyms: ' + error.message, 'error');
        } finally {
            // Re-enable button
            const resetBtn = document.getElementById('resetSynonymsBtn');
            resetBtn.disabled = false;
            resetBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Reset Synonyms';
        }
    }

    async manageSynonyms() {
        try {
            console.log('Opening Kibana synonyms management...');
            
            // Disable button and show loading state
            const manageBtn = document.getElementById('manageSynonymsBtn');
            const originalText = manageBtn.innerHTML;
            manageBtn.disabled = true;
            manageBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
            
            // Fetch the Kibana synonyms URL from the backend
            const response = await fetch('/kibana-synonyms-url', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (data.success && data.url) {
                // Open the Kibana synonyms URL in a new tab
                window.open(data.url, '_blank');
                this.showMessage('Opening Kibana synonyms management in a new tab...', 'success');
            } else {
                this.showMessage('Error: ' + (data.error || 'Failed to get Kibana URL'), 'error');
            }
            
        } catch (error) {
            console.error('Error opening Kibana synonyms:', error);
            this.showMessage('Error opening Kibana synonyms: ' + error.message, 'error');
        } finally {
            // Re-enable button
            const manageBtn = document.getElementById('manageSynonymsBtn');
            manageBtn.disabled = false;
            manageBtn.innerHTML = '<i class="fas fa-cog"></i> Manage Synonyms';
        }
    }

    showMessage(message, type) {
        // Create a temporary message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show position-fixed`;
        messageDiv.style.top = '20px';
        messageDiv.style.right = '20px';
        messageDiv.style.zIndex = '9999';
        messageDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(messageDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.parentNode.removeChild(messageDiv);
            }
        }, 5000);
    }

}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SimpleEcommerceSearch();
});
