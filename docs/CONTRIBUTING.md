# 🤝 Contributing to AI Content Factory

Thank you for your interest in contributing to AI Content Factory! This guide will help you get started with contributing to our open-source AI-powered content creation platform.

---

## 📋 Table of Contents

- [🎯 Ways to Contribute](#-ways-to-contribute)
- [🚀 Getting Started](#-getting-started)
- [🔧 Development Setup](#-development-setup)
- [📝 Contribution Process](#-contribution-process)
- [🎨 Code Style Guidelines](#-code-style-guidelines)
- [🧪 Testing Guidelines](#-testing-guidelines)
- [📚 Documentation](#-documentation)
- [🐛 Bug Reports](#-bug-reports)
- [💡 Feature Requests](#-feature-requests)
- [🔒 Security Issues](#-security-issues)
- [👥 Community Guidelines](#-community-guidelines)

---

## 🎯 Ways to Contribute

We welcome all types of contributions to AI Content Factory:

### 🛠️ **Code Contributions**
- Fix bugs and resolve issues
- Add new features and improvements
- Optimize performance and efficiency
- Enhance security and reliability
- Improve code quality and maintainability

### 📚 **Documentation**
- Improve existing documentation
- Write tutorials and guides
- Create API documentation
- Translate content to other languages
- Fix typos and grammatical errors

### 🐛 **Quality Assurance**
- Report bugs and issues
- Test new features and releases
- Improve test coverage
- Suggest usability improvements
- Validate cross-platform compatibility

### 🎨 **Design & UX**
- Improve user interface design
- Enhance user experience flows
- Create icons and graphics
- Design new components
- Accessibility improvements

### 🌍 **Community**
- Help other users in discussions
- Answer questions on forums
- Create educational content
- Share best practices
- Organize community events

---

## 🚀 Getting Started

### 📋 **Before You Start**

1. **Read our [Code of Conduct](CODE_OF_CONDUCT.md)**
2. **Check existing [issues](https://github.com/ai-content-factory/ai-content-factory/issues) and [pull requests](https://github.com/ai-content-factory/ai-content-factory/pulls)**
3. **Join our [Discord community](https://discord.gg/aicontentfactory) for discussions**
4. **Familiarize yourself with the [project architecture](docs/architecture.md)**

### 🎯 **Good First Issues**

Look for issues labeled with:
- `good first issue` - Perfect for newcomers
- `help wanted` - Community contributions welcome
- `documentation` - Documentation improvements needed
- `bug` - Bug fixes needed
- `enhancement` - Feature improvements

---

## 🔧 Development Setup

### 📋 **Prerequisites**

- **Node.js** 18+ and npm
- **Docker** and Docker Compose
- **Git** for version control
- **PostgreSQL** 13+ (or use Docker)
- **Redis** 6+ (or use Docker)

### ⚡ **Quick Setup**

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR-USERNAME/ai-content-factory.git
cd ai-content-factory

# 2. Add upstream remote
git remote add upstream https://github.com/ai-content-factory/ai-content-factory.git

# 3. Install dependencies
npm install

# 4. Copy environment configuration
cp .env.example .env

# 5. Start development environment
docker-compose up -d

# 6. Run database migrations
npm run db:migrate

# 7. Start the application
npm run dev
```

### 🌐 **Verify Setup**
- Dashboard: http://localhost:3000
- API: http://localhost:5000
- N8N: http://localhost:5678
- Database: localhost:5432

### 🧪 **Run Tests**
```bash
# Run all tests
npm test

# Run specific test suite
npm run test:unit
npm run test:integration
npm run test:e2e

# Run tests with coverage
npm run test:coverage
```

---

## 📝 Contribution Process

### 1. 🍴 **Fork & Branch**

```bash
# Create a new branch for your feature
git checkout -b feature/amazing-feature

# Or for bug fixes
git checkout -b fix/bug-description

# Or for documentation
git checkout -b docs/improve-readme
```

### 2. 🛠️ **Make Changes**

- **Write clean, readable code** following our style guidelines
- **Add tests** for new functionality
- **Update documentation** as needed
- **Follow commit conventions** (see below)

### 3. ✅ **Test Your Changes**

```bash
# Run all tests
npm test

# Check code formatting
npm run lint

# Check TypeScript types
npm run type-check

# Build the project
npm run build
```

### 4. 📤 **Submit Pull Request**

```bash
# Push your branch
git push origin feature/amazing-feature

# Create pull request via GitHub UI
```

### 5. 🔄 **Review Process**

- **Automated checks** must pass (CI/CD)
- **Code review** by maintainers
- **Address feedback** if requested
- **Final approval** and merge

---

## 🎨 Code Style Guidelines

### 📝 **General Principles**

- **Clarity over cleverness** - Write code that's easy to understand
- **Consistency** - Follow existing patterns in the codebase
- **Documentation** - Comment complex logic and decisions
- **Testing** - Write tests for all new functionality
- **Performance** - Consider performance implications

### 🔧 **JavaScript/TypeScript**

```javascript
// ✅ Good
const getUserById = async (userId: string): Promise<User | null> => {
  try {
    const user = await userRepository.findById(userId);
    return user;
  } catch (error) {
    logger.error('Failed to fetch user', { userId, error });
    throw new UserNotFoundError(`User ${userId} not found`);
  }
};

// ❌ Bad
const getUser = async (id) => {
  return await db.user.find(id);
};
```

### 🎨 **React Components**

```jsx
// ✅ Good - TypeScript, clear props, proper error handling
interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  text?: string;
  className?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'medium',
  text = 'Loading...',
  className = ''
}) => {
  return (
    <div className={`spinner spinner-${size} ${className}`}>
      <div className="spinner-animation" />
      {text && <span className="spinner-text">{text}</span>}
    </div>
  );
};
```

### 🐍 **Python (for AI services)**

```python
# ✅ Good
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class TrendAnalyzer:
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
    
    async def analyze_trends(self, trends: List[Trend]) -> List[TrendOpportunity]:
        """Analyze trends and return opportunities."""
        try:
            opportunities = []
            for trend in trends:
                score = await self._calculate_opportunity_score(trend)
                if score > self.MIN_SCORE_THRESHOLD:
                    opportunities.append(TrendOpportunity(trend, score))
            return opportunities
        except Exception as e:
            logger.error(f"Failed to analyze trends: {e}")
            raise TrendAnalysisError("Trend analysis failed")
```

### 📏 **Formatting Rules**

```bash
# Use Prettier for JavaScript/TypeScript
npx prettier --write .

# Use ESLint for linting
npx eslint --fix .

# Use Black for Python
black .

# Use isort for Python imports
isort .
```

---

## 🧪 Testing Guidelines

### 🏗️ **Testing Structure**

```
tests/
├── unit/                 # Unit tests
│   ├── services/
│   ├── components/
│   └── utils/
├── integration/          # Integration tests
│   ├── api/
│   └── database/
├── e2e/                  # End-to-end tests
│   └── workflows/
└── fixtures/             # Test data
    ├── trends.json
    └── users.json
```

### ✅ **Unit Tests**

```javascript
// Example unit test
import { TrendAnalyzer } from '../services/TrendAnalyzer';
import { mockAIService } from '../mocks/ai-service';

describe('TrendAnalyzer', () => {
  let analyzer: TrendAnalyzer;

  beforeEach(() => {
    analyzer = new TrendAnalyzer(mockAIService);
  });

  it('should analyze trends and return opportunities', async () => {
    const trends = [mockTrend({ popularity: 8.5 })];
    const opportunities = await analyzer.analyze(trends);
    
    expect(opportunities).toHaveLength(1);
    expect(opportunities[0].score).toBeGreaterThan(7);
  });

  it('should handle API failures gracefully', async () => {
    mockAIService.analyze.mockRejectedValue(new Error('API Error'));
    
    await expect(analyzer.analyze([mockTrend()])).rejects.toThrow();
  });
});
```

### 🔗 **Integration Tests**

```javascript
// Example integration test
describe('Content Generation API', () => {
  it('should create content from trend data', async () => {
    const trendData = await createTestTrend();
    
    const response = await request(app)
      .post('/api/content/generate')
      .send({ trendId: trendData.id })
      .expect(201);
    
    expect(response.body.content).toBeDefined();
    expect(response.body.metadata).toMatchObject({
      platform: 'youtube',
      duration: expect.any(Number)
    });
  });
});
```

### 🎭 **E2E Tests**

```javascript
// Example E2E test using Playwright
test('complete content creation workflow', async ({ page }) => {
  await page.goto('/dashboard');
  
  // Select trending topic
  await page.click('[data-testid="trend-item"]:first-child');
  await page.click('[data-testid="generate-content"]');
  
  // Wait for generation
  await page.waitForSelector('[data-testid="content-preview"]');
  
  // Verify content was created
  const content = await page.textContent('[data-testid="content-title"]');
  expect(content).toContain('Generated Content');
});
```

### 📊 **Test Coverage**

We aim for **85%+ test coverage**. Check coverage with:

```bash
npm run test:coverage
```

---

## 📚 Documentation

### 📝 **Documentation Types**

1. **Code Documentation**
   - JSDoc comments for functions and classes
   - README files for each service
   - Inline comments for complex logic

2. **API Documentation**
   - OpenAPI/Swagger specifications
   - Request/response examples
   - Error handling documentation

3. **User Documentation**
   - Setup and installation guides
   - User tutorials and how-tos
   - Troubleshooting guides

4. **Developer Documentation**
   - Architecture overviews
   - Deployment guides
   - Contributing guidelines

### ✍️ **Writing Style**

- **Clear and concise** - Get to the point quickly
- **Step-by-step** - Break complex processes into steps
- **Examples** - Include practical examples
- **Screenshots** - Use images for UI-related documentation
- **Links** - Reference related documentation

### 📖 **Documentation Example**

```markdown
## Setting Up YouTube Integration

### Prerequisites
- YouTube account with channel
- Google Cloud Project with YouTube API enabled
- Valid OAuth 2.0 credentials

### Step 1: Create YouTube API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project or create a new one
3. Enable the YouTube Data API v3
4. Create OAuth 2.0 credentials

### Step 2: Configure Environment Variables

```bash
YOUTUBE_CLIENT_ID=your_client_id_here
YOUTUBE_CLIENT_SECRET=your_client_secret_here
YOUTUBE_REDIRECT_URI=http://localhost:5000/auth/youtube/callback
```

### Step 3: Test the Integration

Run the following command to test:

```bash
npm run test:youtube-integration
```

Expected output:
```json
{
  "status": "success",
  "channel": "Your Channel Name",
  "subscribers": 1234
}
```

### Troubleshooting

**Error: Invalid credentials**
- Verify your client ID and secret are correct
- Check that redirect URI matches exactly
```

---

## 🐛 Bug Reports

### 📋 **Before Reporting**

1. **Search existing issues** to avoid duplicates
2. **Check the latest version** - bug might be fixed
3. **Verify it's reproducible** in a clean environment
4. **Gather information** about your environment

### 🚨 **Bug Report Template**

```markdown
## Bug Description
Clear description of what the bug is.

## Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- OS: [e.g. Ubuntu 20.04, Windows 10, macOS 12.1]
- Browser: [e.g. Chrome 96, Firefox 94]
- Node.js Version: [e.g. 18.12.0]
- AI Content Factory Version: [e.g. 1.0.0]

## Additional Context
- Screenshots
- Error logs
- Browser console errors
- Network requests (if relevant)

## Possible Solution
If you have ideas on how to fix this.
```

### 🏷️ **Bug Severity Levels**

- **Critical**: System crash, data loss, security vulnerability
- **High**: Major feature broken, significant impact
- **Medium**: Minor feature issue, workaround available
- **Low**: Cosmetic issue, enhancement request

---

## 💡 Feature Requests

### 🎯 **Feature Request Template**

```markdown
## Feature Summary
Brief description of the feature.

## Problem Statement
What problem does this solve? Who would benefit?

## Proposed Solution
Detailed description of how the feature should work.

## Alternative Solutions
Alternative approaches you've considered.

## User Stories
- As a [user type], I want [functionality] so that [benefit]
- As a [user type], I want [functionality] so that [benefit]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Implementation Notes
Technical considerations, if any.

## Additional Context
- Mockups or wireframes
- Similar features in other tools
- Related issues or discussions
```

### 🗳️ **Feature Prioritization**

Features are prioritized based on:
- **User impact** - How many users would benefit?
- **Business value** - Does it align with project goals?
- **Implementation effort** - How complex is it to build?
- **Community interest** - How much community support?

---

## 🔒 Security Issues

### ⚠️ **Responsible Disclosure**

For security vulnerabilities, please:

1. **DO NOT** create a public GitHub issue
2. **Email us** directly at security@aicontentfactory.com
3. **Include details** about the vulnerability
4. **Wait for response** before public disclosure

### 🛡️ **Security Report Template**

```
Subject: Security Vulnerability Report

Vulnerability Type: [e.g., SQL Injection, XSS, Authentication Bypass]
Affected Component: [e.g., API endpoint, web interface]
Severity: [Critical/High/Medium/Low]

Description:
[Detailed description of the vulnerability]

Steps to Reproduce:
1. [Step 1]
2. [Step 2]
3. [Step 3]

Impact:
[What can an attacker accomplish?]

Suggested Fix:
[If you have suggestions]

Contact Information:
[Your email for follow-up questions]
```

We aim to respond to security reports within **24 hours**.

---

## 👥 Community Guidelines

### 🤝 **Be Respectful**

- **Use inclusive language** and be welcoming to all
- **Respect different viewpoints** and experiences
- **Accept constructive criticism** gracefully
- **Focus on what's best** for the community
- **Show empathy** towards other contributors

### 💬 **Communication**

- **Be clear and concise** in your communication
- **Use appropriate channels** for different types of discussions
- **Search before asking** - your question might be answered already
- **Provide context** when asking for help
- **Help others** when you can

### 🏷️ **Issue and PR Etiquette**

- **Use descriptive titles** and clear descriptions
- **Tag appropriately** with relevant labels
- **Keep discussions on topic** and constructive
- **Be patient** - maintainers are volunteers
- **Follow up** on your contributions

### 📢 **Communication Channels**

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: General questions, ideas
- **Discord**: Real-time chat, community support
- **Email**: Security issues, private matters

---

## 🏆 Recognition

### 🌟 **Contributor Recognition**

We recognize and appreciate all contributors:

- **Contributors file** - All contributors listed
- **Release notes** - Major contributions highlighted
- **Community showcase** - Featured contributions
- **Contributor badges** - GitHub profile recognition

### 🎯 **Contribution Levels**

- **First-time Contributor**: First accepted contribution
- **Regular Contributor**: 5+ accepted contributions
- **Core Contributor**: 25+ contributions, help with reviews
- **Maintainer**: Trusted with write access and releases

---

## ❓ Getting Help

### 🆘 **Need Help?**

- **Documentation**: Check our [docs](https://docs.aicontentfactory.com)
- **GitHub Discussions**: Ask questions in discussions
- **Discord**: Join our community chat
- **Email**: support@aicontentfactory.com

### 📚 **Useful Resources**

- [Project Architecture](docs/architecture.md)
- [API Documentation](docs/api/)
- [Deployment Guide](docs/deployment/)
- [Troubleshooting Guide](docs/guides/troubleshooting.md)

---

## 📜 Legal

### 📄 **Contributor License Agreement**

By contributing to AI Content Factory, you agree that:

- You have the right to license your contribution
- Your contribution is licensed under the MIT License
- You retain copyright to your contributions
- You grant us a license to use your contributions

### 🔗 **License**

All contributions are subject to the [MIT License](LICENSE).

---

## 🙏 Thank You!

Thank you for taking the time to contribute to AI Content Factory! Your contributions help make this project better for everyone.

Every contribution counts, whether it's:
- A single line bug fix
- A new feature implementation
- Documentation improvements
- Helping other users
- Spreading the word

**Together, we're building the future of AI-powered content creation!** 🚀

---

<div align="center">

**Questions? Reach out to us!**

[💬 Discord](https://discord.gg/aicontentfactory) • 
[📧 Email](mailto:support@aicontentfactory.com) • 
[📚 Docs](https://docs.aicontentfactory.com)

</div>