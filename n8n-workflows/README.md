# n8n Workflow Templates

This directory contains pre-built n8n workflow templates for the automation platform.

## Available Workflows

### 1. Content Generation Workflow (`content-generation-workflow.json`)

**Purpose**: Automated daily content generation with human approval

**Features**:
- Scheduled trigger (daily)
- Calls Content API to generate multi-platform content
- Sends Slack notification for review
- Webhook-based approval system
- Publishes approved content

**Setup**:
1. Import the workflow into n8n
2. Configure Slack credentials
3. Set up webhook endpoints
4. Configure environment variables (API_HOST, API_KEY)

### 2. LinkedIn Posting Workflow (`linkedin-posting-workflow.json`)

**Purpose**: Manual or webhook-triggered LinkedIn posting with review

**Features**:
- Webhook trigger for manual posting
- LinkedIn-specific content generation
- Slack review notification
- Direct LinkedIn posting (requires credentials)
- Performance tracking

**Setup**:
1. Import workflow into n8n
2. Configure LinkedIn OAuth credentials
3. Set up Slack webhook
4. Enable LinkedIn posting node
5. Test with webhook trigger

### 3. Analytics Collection Workflow (`analytics-collection-workflow.json`)

**Purpose**: Automated collection of content performance metrics

**Features**:
- Scheduled execution every 6 hours
- Multi-platform analytics collection
- Performance data storage
- Daily summary reports
- Slack notifications with metrics

**Setup**:
1. Import workflow
2. Configure platform API credentials (LinkedIn, Meta)
3. Enable real analytics API calls (currently simulated)
4. Set up Slack for reports

## Environment Variables Required

Configure these in your `.env` file for n8n to access:

```bash
API_HOST=api.yourdomain.com
API_KEY=your-secure-api-key
N8N_HOST=n8n.yourdomain.com
META_ACCESS_TOKEN=your-meta-token
LINKEDIN_ACCESS_TOKEN=your-linkedin-token
```

## Workflow Customization

### Modifying Content Generation

1. **Change Schedule**: Edit the `scheduleTrigger` node
2. **Adjust Platforms**: Modify the platforms array in HTTP request
3. **Custom Prompts**: Update the campaign data in `Set Campaign Data` node
4. **Approval Process**: Customize Slack message format and webhook URLs

### Adding New Platforms

1. Create new HTTP request node for platform API
2. Add platform-specific content formatting
3. Update approval notifications
4. Add platform to analytics collection

### Error Handling

Each workflow includes basic error handling:
- Failed API calls trigger error notifications
- Invalid responses are caught and logged
- Retry logic for transient failures

## Webhook Endpoints

The workflows use these webhook patterns:

- `/webhook/approve/:campaign_id` - Content approval
- `/webhook/reject/:campaign_id` - Content rejection  
- `/webhook/linkedin-post` - Manual LinkedIn posting
- `/webhook/analytics/:content_id` - Performance updates

## Testing Workflows

1. **Content Generation**:
   ```bash
   curl -X POST "https://n8n.yourdomain.com/webhook/test-content" \
     -H "Content-Type: application/json" \
     -d '{"product": "Test Product", "persona": "Test Audience"}'
   ```

2. **LinkedIn Posting**:
   ```bash
   curl -X POST "https://n8n.yourdomain.com/webhook/linkedin-post" \
     -H "Content-Type: application/json" \
     -d '{"product": "Product", "persona": "Audience", "context": "Test post"}'
   ```

## Integration with Content API

All workflows integrate with the Content API endpoints:

- `POST /generate-campaign` - Content generation
- `POST /webhook/n8n` - Webhook callbacks
- `POST /analytics/performance` - Performance tracking
- `GET /analytics/report/{campaign_id}` - Analytics reports

## Monitoring and Debugging

1. **Execution History**: Check n8n execution history for failed runs
2. **Webhook Logs**: Monitor webhook endpoint responses
3. **API Logs**: Check Content API logs for integration issues
4. **Slack Notifications**: Set up alerts for workflow failures

## Advanced Features

### Conditional Content Publishing

Modify workflows to include:
- Content quality scoring
- A/B testing selection
- Time zone optimization
- Platform-specific formatting

### Multi-stage Approval

Add additional approval stages:
- Legal review for compliance
- Brand guideline checks
- Manager approval
- Performance predictions

### Dynamic Scheduling

Enhance with:
- Optimal posting time detection
- Audience activity analysis
- Competitor posting analysis
- Seasonal content adjustments

## Backup and Version Control

1. Export workflows regularly from n8n
2. Commit changes to this repository
3. Document modifications in commit messages
4. Test workflows before deploying to production

## Support

For workflow issues:
1. Check n8n execution logs
2. Verify API connectivity
3. Test individual nodes
4. Review webhook configurations
5. Check environment variable values