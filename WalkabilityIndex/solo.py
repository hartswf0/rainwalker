import os
from bs4 import BeautifulSoup
from pathlib import Path
import json
import re

class TufteIntegrator:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.tufte_dir = self.base_dir / 'tufte_tests'
        self.structure = {
            'overview': ['creator.html', 'temporal.html', 'geographic.html'],  # Added geographic.html
            'access': ['instructions.html', 'requirements.html'],
            'standards': ['structure.html'],
            'codebook': ['fields.html'],
            'context': ['analysis.html'],
            'uses': ['applications.html'],
            'sources': ['references.html']
        }
        
    def extract_content(self, file_path):
        """Extract the content and resources from a Tufte page."""
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Extract styles
            styles = []
            for style in soup.find_all('style'):
                if style.string:
                    # Process styles to work in dark mode
                    css = style.string
                    # Convert light theme colors to CSS variables
                    css = re.sub(r'background:\s*#fff', 'background: var(--bg-color)', css)
                    css = re.sub(r'color:\s*#333', 'color: var(--text-color)', css)
                    css = re.sub(r'background-color:\s*#fff', 'background-color: var(--bg-color)', css)
                    styles.append(css)
            
            # Extract scripts
            scripts = []
            for script in soup.find_all('script'):
                if script.get('src'):
                    scripts.append({'src': script['src']})
                elif script.string:
                    scripts.append({'content': script.string})
            
            # Extract main content
            main_content = soup.find('body')
            if main_content:
                for script in main_content.find_all('script'):
                    script.decompose()
                content = str(main_content).replace('<body>', '').replace('</body>', '').strip()
                
                # Wrap content in a container for proper styling
                content = f'<div class="tufte-content">{content}</div>'
            
            return {
                'styles': styles,
                'scripts': scripts,
                'content': content
            }
    
    def generate_integrated_html(self):
        """Generate the integrated datawalker HTML."""
        template = """
<!DOCTYPE html>
<html>
<head>
    <title>Walking Through Data | Atlanta Walkability</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://unpkg.com/intersection-observer"></script>
    <script src="https://unpkg.com/scrollama"></script>
    <style>
        :root {
            --text: #f0f0f0;
            --background: #111;
            --highlight: #ffd700;
            --muted: #666;
            --spacing: 2rem;
            --transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            --bg-color: var(--background);
            --text-color: var(--text);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background: var(--background);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.6;
            overflow-x: hidden;
        }

        .data-path {
            position: fixed;
            top: 0;
            left: 0;
            width: 4px;
            height: 100vh;
            background: var(--muted);
            margin-left: 2rem;
            z-index: 100;
        }

        .data-path::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            background: var(--highlight);
            transition: height 0.5s ease;
        }

        .section {
            min-height: 100vh;
            padding: 2rem 4rem 2rem 6rem;
            display: flex;
            flex-direction: column;
            justify-content: center;
            position: relative;
        }

        .node {
            position: absolute;
            left: 2rem;
            width: 1rem;
            height: 1rem;
            background: var(--muted);
            border-radius: 50%;
            transform: translateX(-0.5rem);
            transition: var(--transition);
            z-index: 101;
        }

        .node.active {
            background: var(--highlight);
            transform: translateX(-0.5rem) scale(1.2);
        }

        .content {
            max-width: 1200px;
            margin: 0 auto;
            opacity: 0.3;
            transform: translateX(20px);
            transition: var(--transition);
        }

        .section.active .content {
            opacity: 1;
            transform: translateX(0);
        }

        h1 {
            font-size: 2.5em;
            margin-bottom: var(--spacing);
            font-weight: 300;
            color: var(--text);
        }

        h2 {
            font-size: 2em;
            margin-bottom: calc(var(--spacing) * 0.75);
            color: var(--highlight);
            font-weight: 300;
        }

        p {
            margin-bottom: var(--spacing);
            color: var(--text);
            max-width: 65ch;
            font-size: 1.1em;
            line-height: 1.6;
        }

        .tufte-container {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            margin: var(--spacing) 0;
            padding: var(--spacing);
            transition: var(--transition);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }

        .tufte-container:hover {
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        }

        .tufte-content {
            color: var(--text);
        }

        .tufte-content img,
        .tufte-content svg {
            filter: invert(0.9);
        }

        .tufte-content .chart text {
            fill: var(--text);
        }

        .tufte-content .chart path,
        .tufte-content .chart line {
            stroke: var(--text);
        }

        .progress-label {
            position: fixed;
            left: 4rem;
            top: 50%;
            transform: translateY(-50%);
            font-size: 0.9em;
            color: var(--muted);
            transition: var(--transition);
            pointer-events: none;
            z-index: 102;
        }

        .progress-label.active {
            color: var(--highlight);
        }

        .scroll-prompt {
            position: fixed;
            bottom: 2rem;
            left: 50%;
            transform: translateX(-50%);
            color: var(--muted);
            font-size: 0.9em;
            opacity: 0.7;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 0.5rem;
            z-index: 102;
        }

        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
            40% { transform: translateY(-10px); }
            60% { transform: translateY(-5px); }
        }

        .scroll-arrow {
            animation: bounce 1.5s infinite;
        }

        /* Tufte-specific dark mode adjustments */
        .tufte-content {
            --text-color: var(--text);
            --bg-color: transparent;
            --link-color: var(--highlight);
        }

        .tufte-content a {
            color: var(--highlight);
            text-decoration: none;
            border-bottom: 1px solid var(--highlight);
            transition: var(--transition);
        }

        .tufte-content a:hover {
            color: var(--text);
            border-color: var(--text);
        }

        /* Enhanced visibility for charts and visualizations */
        .tufte-content .axis text {
            fill: var(--text);
            font-size: 12px;
        }

        .tufte-content .axis line,
        .tufte-content .axis path {
            stroke: var(--muted);
        }

        .tufte-content .grid line {
            stroke: var(--muted);
            stroke-opacity: 0.1;
        }

        /* Remove any existing navigation buttons */
        .nav-buttons,
        .control-button,
        .controls {
            display: none !important;
        }
    </style>
    <!-- Tufte styles will be injected here -->
    {{TUFTE_STYLES}}
</head>
<body>
    <div class="data-path"></div>
    <div class="progress-label">Overview</div>

    {{SECTIONS}}

    <div class="scroll-prompt">
        Scroll to explore <span class="scroll-arrow">↓</span>
    </div>

    <!-- D3 and other scripts -->
    {{TUFTE_SCRIPTS}}
    
    <script>
        // Initialize scrollama
        const scroller = scrollama();
        
        // Setup scroll interactions
        scroller
            .setup({
                step: '.section',
                offset: 0.5,
                debug: false
            })
            .onStepEnter(response => {
                // Update active section
                document.querySelectorAll('.section').forEach(section => {
                    section.classList.remove('active');
                });
                response.element.classList.add('active');

                // Update nodes
                const nodes = document.querySelectorAll('.node');
                nodes.forEach((node, index) => {
                    if (index <= response.index) {
                        node.classList.add('active');
                    } else {
                        node.classList.remove('active');
                    }
                });

                // Update progress path
                const progress = ((response.index + 1) / document.querySelectorAll('.section').length) * 100;
                document.querySelector('.data-path::after').style.height = `${progress}%`;

                // Update label
                const label = document.querySelector('.progress-label');
                label.textContent = response.element.dataset.title;
                label.classList.add('active');
            })
            .onStepExit(response => {
                if (response.direction === 'up') {
                    response.element.classList.remove('active');
                    document.querySelector('.progress-label').classList.remove('active');
                }
            });

        // Handle resize
        window.addEventListener('resize', scroller.resize);

        // Hide scroll prompt when scrolling starts
        let scrollTimeout;
        window.addEventListener('scroll', () => {
            const prompt = document.querySelector('.scroll-prompt');
            prompt.style.opacity = '0';
            
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                prompt.style.opacity = '0.7';
            }, 1000);
        });

        // Ensure all D3 charts use the correct colors
        function updateChartColors() {
            d3.selectAll('.chart text').style('fill', 'var(--text)');
            d3.selectAll('.chart path').style('stroke', 'var(--text)');
            d3.selectAll('.chart line').style('stroke', 'var(--text)');
        }

        // Run after all content is loaded
        window.addEventListener('load', updateChartColors);
    </script>
</body>
</html>
"""
        
        # Collect all Tufte content
        all_styles = set()
        all_scripts = []
        sections_html = []
        
        for section, files in self.structure.items():
            section_content = []
            for file in files:
                # Find the file in the section subdirectory
                file_path = None
                for subdir in self.tufte_dir.glob('*'):
                    if subdir.is_dir():
                        potential_path = subdir / file
                        if potential_path.exists():
                            file_path = potential_path
                            break
                
                if file_path:
                    content = self.extract_content(file_path)
                    all_styles.update(content['styles'])
                    all_scripts.extend(content['scripts'])
                    section_content.append(content['content'])
            
            # Create section HTML
            section_html = f"""
            <section class="section" data-step="{section}" data-title="{section.title()}">
                <div class="node"></div>
                <div class="content">
                    <div class="tufte-container">
                        {''.join(section_content)}
                    </div>
                </div>
            </section>
            """
            sections_html.append(section_html)
        
        # Generate scripts HTML
        scripts_html = []
        for script in all_scripts:
            if 'src' in script:
                scripts_html.append(f'<script src="{script["src"]}"></script>')
            elif 'content' in script:
                scripts_html.append(f'<script>{script["content"]}</script>')
        
        # Replace placeholders in template
        html = template.replace('{{TUFTE_STYLES}}', 
                              f'<style>{"".join(all_styles)}</style>')
        html = html.replace('{{TUFTE_SCRIPTS}}', '\n'.join(scripts_html))
        html = html.replace('{{SECTIONS}}', '\n'.join(sections_html))
        
        return html
    
    def save_integrated_html(self, output_file='datawalker-solo.html'):
        """Save the integrated HTML to a file."""
        html = self.generate_integrated_html()
        with open(self.base_dir / output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Created integrated file: {output_file}")

def main():
    base_dir = "/Users/gaia/Downloads/WalkabilityIndex"
    integrator = TufteIntegrator(base_dir)
    integrator.save_integrated_html()

if __name__ == "__main__":
    main()
