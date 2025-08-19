/**
 * Image optimization utilities for reducing bundle size and improving performance
 */

/**
 * Lazy load images with intersection observer
 */
export function setupLazyLoading(): void {
  if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target as HTMLImageElement;
          if (img.dataset.src) {
            img.src = img.dataset.src;
            img.classList.remove('lazy');
            observer.unobserve(img);
          }
        }
      });
    });

    // Observe all images with data-src attribute
    document.querySelectorAll('img[data-src]').forEach(img => {
      imageObserver.observe(img);
    });
  }
}

/**
 * Generate responsive image srcset for different screen sizes
 */
export function generateResponsiveImageSrc(
  basePath: string, 
  sizes: number[] = [320, 640, 1024, 1280]
): string {
  return sizes
    .map(size => `${basePath}?w=${size} ${size}w`)
    .join(', ');
}

/**
 * Preload critical images
 */
export function preloadCriticalImages(imagePaths: string[]): void {
  imagePaths.forEach(path => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.as = 'image';
    link.href = path;
    document.head.appendChild(link);
  });
}

/**
 * Convert image to WebP format if supported
 */
export function getOptimizedImageUrl(originalUrl: string): string {
  // Check if browser supports WebP
  const supportsWebP = (() => {
    const canvas = document.createElement('canvas');
    canvas.width = 1;
    canvas.height = 1;
    return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
  })();

  if (supportsWebP && originalUrl.includes('.jpg')) {
    return originalUrl.replace('.jpg', '.webp');
  }
  
  return originalUrl;
}
