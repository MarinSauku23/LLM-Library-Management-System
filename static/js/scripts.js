window.addEventListener('DOMContentLoaded', () => {
    /*
     tracks the previous scroll position to detect scroll direction
     */
    let lastScrollTop = 0;

    const mainNav = document.getElementById('mainNav');
    const headerHeight = mainNav.clientHeight;

    window.addEventListener('scroll', function() {
        // current vertical scroll position
        const currentScroll = window.scrollY;

        if ( currentScroll < lastScrollTop) {
            // scrolling Up
            if (currentScroll > 0 && mainNav.classList.contains('is-fixed')) {
                mainNav.classList.add('is-visible');
            } else {
                mainNav.classList.remove('is-visible', 'is-fixed');
            }
        } else {
            // Scrolling Down
            mainNav.classList.remove(['is-visible']);

            if (currentScroll > headerHeight && !mainNav.classList.contains('is-fixed')) {
                mainNav.classList.add('is-fixed');
            }
        }
        lastScrollTop = currentScroll;
    });
})


