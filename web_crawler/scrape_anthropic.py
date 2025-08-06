import asyncio
import os
import sys
import io
from crawl4ai import AsyncWebCrawler
from Crawl4ai import create_filename_from_url
from datetime import datetime

# Set stdout and stderr to utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

async def main():
    urls = [
        "https://www.anthropic.com/research/persona-vectors",
        "https://www.anthropic.com/research/project-vend-1",
        "https://www.anthropic.com/research/agentic-misalignment",
        "https://www.anthropic.com/research/confidential-inference-trusted-vms",
        "https://www.anthropic.com/research/shade-arena-sabotage-monitoring",
        "https://www.anthropic.com/research/open-source-circuit-tracing",
        "https://www.anthropic.com/research/impact-software-development",
        "https://www.anthropic.com/research/exploring-model-welfare",
        "https://www.anthropic.com/research/values-wild",
        "https://www.anthropic.com/news/anthropic-education-report-how-university-students-use-claude",
        "https://www.anthropic.com/research/reasoning-models-dont-say-think",
        "https://www.anthropic.com/news/anthropic-economic-index-insights-from-claude-sonnet-3-7",
        "https://www.anthropic.com/news/tracing-thoughts-language-model",
        "https://www.anthropic.com/research/auditing-hidden-objectives",
        "https://www.anthropic.com/research/forecasting-rare-behaviors",
        "https://www.anthropic.com/news/visible-extended-thinking",
        "https://www.anthropic.com/research/crosscoder-model-diffing",
        "https://www.anthropic.com/news/the-anthropic-economic-index",
        "https://www.anthropic.com/research/constitutional-classifiers",
        "https://www.anthropic.com/engineering/building-effective-agents",
        "https://www.anthropic.com/research/alignment-faking",
        "https://www.anthropic.com/research/clio",
        "https://www.anthropic.com/research/statistical-approach-to-model-evals",
        "https://www.anthropic.com/engineering/swe-bench-sonnet",
        "https://www.anthropic.com/research/evaluating-feature-steering",
        "https://www.anthropic.com/news/developing-computer-use",
        "https://www.anthropic.com/research/sabotage-evaluations",
        "https://www.anthropic.com/research/features-as-classifiers",
        "https://www.anthropic.com/research/circuits-updates-september-2024",
        "https://www.anthropic.com/research/circuits-updates-august-2024",
        "https://www.anthropic.com/research/circuits-updates-july-2024",
        "https://www.anthropic.com/research/circuits-updates-june-2024",
        "https://www.anthropic.com/research/reward-tampering",
        "https://www.anthropic.com/research/engineering-challenges-interpretability",
        "https://www.anthropic.com/research/claude-character",
        "https://www.anthropic.com/news/testing-and-mitigating-elections-related-risks",
        "https://www.anthropic.com/research/mapping-mind-language-model",
        "https://www.anthropic.com/research/circuits-updates-april-2024",
        "https://www.anthropic.com/research/probes-catch-sleeper-agents",
        "https://www.anthropic.com/research/measuring-model-persuasiveness",
        "https://www.anthropic.com/research/many-shot-jailbreaking",
        "https://www.anthropic.com/research/transformer-circuits",
        "https://www.anthropic.com/research/sleeper-agents-training-deceptive-llms-that-persist-through-safety-training",
        "https://www.anthropic.com/news/evaluating-and-mitigating-discrimination-in-language-model-decisions",
        "https://www.anthropic.com/research/specific-versus-general-principles-for-constitutional-ai",
        "https://www.anthropic.com/research/towards-understanding-sycophancy-in-language-models",
        "https://www.anthropic.com/research/collective-constitutional-ai-aligning-a-language-model-with-public-input",
        "https://www.anthropic.com/research/decomposing-language-models-into-understandable-components",
        "https://www.anthropic.com/research/towards-monosemanticity-decomposing-language-models-with-dictionary-learning",
        "https://www.anthropic.com/news/evaluating-ai-systems",
        "https://www.anthropic.com/research/influence-functions",
        "https://www.anthropic.com/research/studying-large-language-model-generalization-with-influence-functions",
        "https://www.anthropic.com/research/measuring-faithfulness-in-chain-of-thought-reasoning",
        "https://www.anthropic.com/research/question-decomposition-improves-the-faithfulness-of-model-generated-reasoning",
        "https://www.anthropic.com/research/towards-measuring-the-representation-of-subjective-global-opinions-in-language-models",
        "https://www.anthropic.com/research/circuits-updates-may-2023",
        "https://www.anthropic.com/research/interpretability-dreams",
        "https://www.anthropic.com/research/distributed-representations-composition-superposition",
        "https://www.anthropic.com/research/privileged-bases-in-the-transformer-residual-stream",
        "https://www.anthropic.com/research/the-capacity-for-moral-self-correction-in-large-language-models",
        "https://www.anthropic.com/research/superposition-memorization-and-double-descent",
        "https://www.anthropic.com/research/discovering-language-model-behaviors-with-model-written-evaluations",
        "https://www.anthropic.com/research/constitutional-ai-harmlessness-from-ai-feedback",
        "https://www.anthropic.com/research/measuring-progress-on-scalable-oversight-for-large-language-models",
        "https://www.anthropic.com/research/toy-models-of-superposition",
        "https://www.anthropic.com/research/red-teaming-language-models-to-reduce-harms-methods-scaling-behaviors-and-lessons-learned",
        "https://www.anthropic.com/research/language-models-mostly-know-what-they-know",
        "https://www.anthropic.com/research/softmax-linear-units",
        "https://www.anthropic.com/research/scaling-laws-and-interpretability-of-learning-from-repeated-data",
        "https://www.anthropic.com/research/training-a-helpful-and-harmless-assistant-with-reinforcement-learning-from-human-feedback",
        "https://www.anthropic.com/research/in-context-learning-and-induction-heads",
        "https://www.anthropic.com/research/predictability-and-surprise-in-large-generative-models",
        "https://www.anthropic.com/research/a-mathematical-framework-for-transformer-circuits",
        "https://www.anthropic.com/research/a-general-language-assistant-as-a-laboratory-for-alignment",
    ]

    output_dir = "anthropic"
    os.makedirs(output_dir, exist_ok=True)

    async with AsyncWebCrawler() as crawler:
        for url in urls:
            try:
                result = await crawler.arun(url=url)
                filename = create_filename_from_url(url)
                filepath = os.path.join(output_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"# {url}\n\n")
                    f.write(f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                    f.write(result.markdown)
                print(f"Content saved to: {filepath}")
            except Exception as e:
                print(f"Failed to process {url}: {e}")

if __name__ == "__main__":
    asyncio.run(main())