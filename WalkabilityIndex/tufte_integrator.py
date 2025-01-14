import os
from bs4 import BeautifulSoup
from pathlib import Path
import json
import re
import shutil

class TufteIntegrator:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.tufte_dir = self.base_dir / 'tufte_tests'
        self.sections = [
            'overview',
            'access',
            'standards',
            'codebook',
            'context',
            'uses',
            'sources'
        ]
    
    def get_all_html_files(self):
        """Get all HTML files in the tufte_tests directory."""
        html_files = []
        for section in self.sections:
            section_dir = self.tufte_dir / section
            if section_dir.exists():
                html_files.extend(list(section_dir.glob('*.html')))
        return html_files
    
    def extract_content(self, file_path):
        """Extract content from a Tufte page, preserving scripts and data."""
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Remove navigation elements
            for nav in soup.find_all(class_=['nav-buttons', 'control-button', 'controls', 'navigation']):
                nav.decompose()
            
            # Extract styles
            styles = []
            for style in soup.find_all('style'):
                if style.string:
                    styles.append(style.string)
            
            # Extract scripts and preserve D3 initialization
            scripts = []
            for script in soup.find_all('script'):
                if script.get('src'):
                    # Add all necessary D3 dependencies
                    src = script['src']
                    if any(lib in src for lib in ['d3', 'topojson']):
                        scripts.append({'src': src})
                elif script.string:
                    # Fix data file paths in the script
                    js_content = script.string
                    js_content = js_content.replace('../../', '')
                    js_content = js_content.replace('../', '')
                    scripts.append({'content': js_content})
            
            # Extract main content
            main_content = soup.find('body')
            if main_content:
                # Remove navigation
                for nav in main_content.find_all('div', class_='navigation'):
                    nav.decompose()
                
                # Keep the original structure for visualization containers
                content = str(main_content).replace('<body>', '').replace('</body>', '').strip()
                
                # Create a container for the content
                section_name = file_path.parent.name
                content = f'<div class="tufte-content" data-section="{section_name}">{content}</div>'
            
            return {
                'styles': styles,
                'scripts': scripts,
                'content': content,
                'section': file_path.parent.name
            }
    
    def generate_integrated_html(self):
        """Generate the integrated datawalker HTML with light theme."""
        template = """
<!DOCTYPE html>
<html>
<head>
    <title>Walking Through Data | Atlanta Walkability</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://d3js.org/d3-geo.v3.min.js"></script>
    <script src="https://d3js.org/topojson.v3.min.js"></script>
    <script src="https://unpkg.com/intersection-observer"></script>
    <script src="https://unpkg.com/scrollama"></script>
    <style>
        :root {
            --text: #222;
            --background: #fff;
            --highlight: #1a5f7a;
            --muted: #666;
            --spacing: 2rem;
            --transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            
            /* Tufte-inspired colors */
            --tufte-background: #fffff8;
            --tufte-text: #111;
            --tufte-gray: #666;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background: var(--background);
            color: var(--text);
            font-family: "ET Book", Georgia, serif;
            line-height: 1.6;
            overflow-x: hidden;
        }

        /* Progress tracking */
        .data-path {
            position: fixed;
            top: 0;
            left: 0;
            width: 3px;
            height: 100vh;
            background: #eee;
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
        }

        .node {
            position: absolute;
            left: 2rem;
            width: 0.75rem;
            height: 0.75rem;
            background: #eee;
            border-radius: 50%;
            transform: translateX(-0.375rem);
            transition: var(--transition);
            z-index: 101;
        }

        .node.active {
            background: var(--highlight);
            transform: translateX(-0.375rem) scale(1.2);
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

        /* Typography */
        h1, h2, h3, h4, h5, h6 {
            font-weight: 400;
            margin-bottom: var(--spacing);
            color: var(--text);
        }

        h1 { 
            font-size: 2.5em;
            font-style: italic;
        }

        h2 { 
            font-size: 2em;
            color: var(--highlight);
        }

        p {
            margin-bottom: var(--spacing);
            max-width: 65ch;
            font-size: 1.1em;
            line-height: 1.7;
            color: var(--text);
        }

        /* Visualization containers */
        .chart-container {
            background: var(--tufte-background);
            border-radius: 4px;
            margin: var(--spacing) 0;
            padding: var(--spacing);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            height: 400px;
            width: 100%;
        }

        .chart-container svg {
            width: 100%;
            height: 100%;
        }

        /* Map styles */
        .map-container {
            position: relative;
            height: 600px;
            background: var(--tufte-background);
            border-radius: 4px;
            margin: var(--spacing) 0;
            padding: var(--spacing);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }

        .map-container svg {
            width: 100%;
            height: 100%;
        }

        .legend {
            position: absolute;
            bottom: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.9);
            padding: 10px;
            border: 1px solid #ddd;
            z-index: 1000;
        }

        /* Grid layouts */
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: var(--spacing);
            margin: var(--spacing) 0;
        }

        .grid-item {
            background: var(--tufte-background);
            padding: var(--spacing);
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }

        /* Code samples */
        .code-sample {
            background: var(--background);
            padding: 1rem;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.9em;
            color: var(--tufte-text);
            white-space: pre;
            overflow-x: auto;
            margin: var(--spacing) 0;
        }

        /* Tables */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: var(--spacing) 0;
            background: var(--tufte-background);
            border-radius: 4px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }

        th, td {
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid var(--background);
        }

        th {
            background: var(--highlight);
            color: var(--background);
            font-weight: normal;
            font-style: italic;
        }

        tr:hover {
            background: var(--background);
        }

        /* Progress label */
        .progress-label {
            position: fixed;
            left: 4rem;
            top: 50%;
            transform: translateY(-50%);
            font-size: 0.9em;
            color: var(--muted);
            font-style: italic;
            transition: var(--transition);
            pointer-events: none;
            z-index: 102;
        }

        .progress-label.active {
            color: var(--highlight);
        }

        /* Scroll prompt */
        .scroll-prompt {
            position: fixed;
            bottom: 2rem;
            left: 50%;
            transform: translateX(-50%);
            color: var(--muted);
            font-size: 0.9em;
            font-style: italic;
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
            color: var(--highlight);
        }
    </style>
    {{TUFTE_STYLES}}
</head>
<body>
    <div class="data-path"></div>
    <div class="progress-label">Overview</div>

    {{SECTIONS}}

    <div class="scroll-prompt">
        Scroll to explore <span class="scroll-arrow">↓</span>
    </div>

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
                document.querySelector('.data-path').style.setProperty('--progress', `${progress}%`);

                // Update label
                const label = document.querySelector('.progress-label');
                label.textContent = response.element.dataset.title || 'Overview';
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

        // Initialize all visualizations
        document.addEventListener('DOMContentLoaded', () => {
            // Re-run any D3 visualizations that need window dimensions
            const charts = document.querySelectorAll('[id*="chart"], [id*="map"], [id*="graph"]');
            charts.forEach(chart => {
                const event = new Event('resize');
                window.dispatchEvent(event);
            });
        });
    </script>
</body>
</html>
"""
        
        # Collect all content
        all_styles = set()
        all_scripts = []
        sections_html = []
        
        # Process each HTML file
        html_files = self.get_all_html_files()
        for file_path in sorted(html_files):
            content = self.extract_content(file_path)
            
            # Add styles and scripts
            all_styles.update(content['styles'])
            all_scripts.extend(content['scripts'])
            
            # Create section HTML
            section_html = f"""
            <section class="section" data-step="{content['section']}" data-title="{content['section'].title()}">
                <div class="node"></div>
                <div class="content">
                    {content['content']}
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
    
    def save_integrated_html(self, output_file='datawalker-dubstep.html'):
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
