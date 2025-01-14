import os
from bs4 import BeautifulSoup
from pathlib import Path
import json

class TuftePageAnalyzer:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.tufte_dir = self.base_dir / 'tufte_tests'
        self.pages = {}
        self.structure = {
            'overview': ['creator.html', 'temporal.html'],
            'access': ['instructions.html', 'requirements.html'],
            'standards': ['structure.html'],
            'codebook': ['fields.html'],
            'context': ['analysis.html'],
            'uses': ['applications.html'],
            'sources': ['references.html']
        }
        
    def analyze_page(self, file_path):
        """Analyze a single Tufte page for its components and dependencies."""
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Extract metadata
            title = soup.title.string if soup.title else ""
            
            # Extract styles
            styles = []
            for style in soup.find_all('style'):
                if style.string:
                    styles.append(style.string)
            
            # Extract scripts
            scripts = []
            for script in soup.find_all('script'):
                if script.get('src'):
                    scripts.append({'src': script['src']})
                elif script.string:
                    scripts.append({'content': script.string})
            
            # Extract main content structure
            main_content = soup.find('body')
            if main_content:
                # Remove scripts from content analysis
                for script in main_content.find_all('script'):
                    script.decompose()
                
                # Analyze content structure
                sections = []
                for section in main_content.find_all(['section', 'div'], class_=True):
                    sections.append({
                        'class': section.get('class'),
                        'id': section.get('id'),
                        'type': section.name
                    })
            
            return {
                'title': title,
                'styles': styles,
                'scripts': scripts,
                'sections': sections,
                'dependencies': {
                    'external': [s['src'] for s in scripts if 'src' in s],
                    'internal': []  # Add internal dependencies if found
                }
            }
    
    def analyze_all_pages(self):
        """Analyze all Tufte pages and their relationships."""
        for section, files in self.structure.items():
            section_pages = []
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
                    analysis = self.analyze_page(file_path)
                    analysis['file'] = str(file_path.relative_to(self.tufte_dir))
                    section_pages.append(analysis)
            
            self.pages[section] = section_pages
    
    def generate_report(self):
        """Generate a detailed report of the analysis."""
        report = {
            'sections': {},
            'global_dependencies': set(),
            'style_patterns': set(),
            'interaction_patterns': []
        }
        
        for section, pages in self.pages.items():
            report['sections'][section] = {
                'pages': len(pages),
                'total_scripts': sum(len(page['scripts']) for page in pages),
                'total_styles': sum(len(page['styles']) for page in pages),
                'files': [page['file'] for page in pages]
            }
            
            # Collect global dependencies
            for page in pages:
                report['global_dependencies'].update(page['dependencies']['external'])
        
        return report
    
    def save_analysis(self, output_file='tufte_analysis.json'):
        """Save the analysis to a JSON file."""
        report = self.generate_report()
        
        # Convert sets to lists for JSON serialization
        report['global_dependencies'] = list(report['global_dependencies'])
        report['style_patterns'] = list(report['style_patterns'])
        
        with open(self.base_dir / output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

def main():
    base_dir = "/Users/gaia/Downloads/WalkabilityIndex"
    analyzer = TuftePageAnalyzer(base_dir)
    analyzer.analyze_all_pages()
    analyzer.save_analysis()
    print("Analysis complete. Check tufte_analysis.json for results.")

if __name__ == "__main__":
    main()
