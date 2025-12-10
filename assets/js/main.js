$(function() {
    $(".gif").gifplayer();

    // Show footnote tooltip on hover of tooltip reference
    const footnoteLinks = document.querySelectorAll('a.footnote[role="doc-noteref"]');

    footnoteLinks.forEach(link => {
        let hideTimeout = null;

        const showTooltip = function() {
            // Clear any pending hide timeout
            if (hideTimeout) {
                clearTimeout(hideTimeout);
                hideTimeout = null;
            }

            // Don't create a new tooltip if one already exists
            if (this._footnoteTooltip) {
                return;
            }

            const footnoteId = this.getAttribute("href").substring(1); // Remove the "#"
            const footnoteElement = document.getElementById(footnoteId);

            if (footnoteElement) {
                // Get footnote content (excluding the back-reference link)
                const footnoteContent = footnoteElement.querySelector("p");

                // Clone the content and remove the back-reference
                const content = footnoteContent.cloneNode(true);
                const clonedBackLink = content.querySelector(".reversefootnote");
                if (clonedBackLink) {
                    clonedBackLink.remove();
                }

                // Create tooltip
                const tooltip = document.createElement("div");
                tooltip.className = "footnote-tooltip";
                tooltip.innerHTML = content.innerHTML;
                document.body.appendChild(tooltip);

                // Position tooltip
                const rect = this.getBoundingClientRect();
                const tooltipRect = tooltip.getBoundingClientRect();

                // Position below the footnote reference
                let left = rect.left + window.scrollX;
                let top = rect.bottom + window.scrollY + 5;

                // Adjust if tooltip goes off-screen to the right
                if (left + tooltipRect.width > window.innerWidth) {
                    left = window.innerWidth - tooltipRect.width - 10;
                }

                // Adjust if tooltip goes off-screen to the left
                if (left < 0) {
                    left = 10;
                }

                tooltip.style.left = left + "px";
                tooltip.style.top = top + "px";

                // Store tooltip reference on the link
                this._footnoteTooltip = tooltip;

                // Keep tooltip visible when hovering over it
                tooltip.addEventListener("mouseenter", function() {
                    if (hideTimeout) {
                        clearTimeout(hideTimeout);
                        hideTimeout = null;
                    }
                });

                tooltip.addEventListener("mouseleave", function() {
                    hideTooltip.call(link);
                });
            }
        };

        const hideTooltip = function() {
            // Use a small delay to allow mouse to move from link to tooltip
            hideTimeout = setTimeout(() => {
                if (this._footnoteTooltip) {
                    this._footnoteTooltip.remove();
                    this._footnoteTooltip = null;
                }
                hideTimeout = null;
            }, 100);
        };

        link.addEventListener("mouseenter", showTooltip);
        link.addEventListener("mouseleave", hideTooltip);
    });
});
