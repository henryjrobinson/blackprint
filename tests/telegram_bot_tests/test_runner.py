"""Automated test runner for Telegram bot"""
import asyncio
import logging
from datetime import datetime
import json
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from test_config import (
    API_ID, API_HASH, BOT_TOKEN, BOT_USERNAME,
    TEST_SCENARIOS, DYNAMIC_TEST_CASES
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_bot_tests.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TelegramBotTester:
    def __init__(self):
        self.client = TelegramClient(
            'bot_tester_session',
            API_ID,
            API_HASH
        )
        self.test_results = []
        self.error_log = []
        
    async def start(self):
        """Start the client and get the bot entity"""
        await self.client.start()
        self.bot = await self.client.get_entity(BOT_USERNAME)
        
    async def send_command(self, command):
        """Send a command to the bot and wait for response"""
        try:
            # Log the command being sent
            logger.info(f"Sending command: {command}")
            
            await self.client.send_message(self.bot, command)
            # Wait for bot response with timeout
            await asyncio.sleep(3)  # Increased wait time for reliability
            
            # Get latest messages
            messages = await self.client(GetHistoryRequest(
                peer=self.bot,
                limit=1,
                offset_date=None,
                offset_id=0,
                max_id=0,
                min_id=0,
                add_offset=0,
                hash=0
            ))
            
            if messages.messages:
                response = messages.messages[0].message
                logger.info(f"Received response: {response}")
                return response
            
            logger.warning(f"No response received for command: {command}")
            return None
            
        except Exception as e:
            error_msg = f"Error sending command {command}: {str(e)}"
            logger.error(error_msg)
            self.error_log.append({
                'command': command,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            return f"ERROR: {str(e)}"
            
    def validate_response(self, response, expected):
        """Validate response against expected content"""
        if not response:
            return False
            
        if isinstance(expected, str):
            return expected.lower() in response.lower()
        elif isinstance(expected, list):
            return all(exp.lower() in response.lower() for exp in expected)
        return False
            
    async def run_test_scenario(self, scenario):
        """Run a single test scenario"""
        logger.info(f"\nRunning test scenario: {scenario['name']}")
        results = []
        
        # Handle dynamic test cases
        if scenario['name'] == 'Random Stock Historical Tests':
            # Generate random stock and date
            stock, date = DYNAMIC_TEST_CASES['random_historical']['generate']()
            scenario['commands'] = [f'/historical {stock} {date}']
            scenario['expected_responses'] = ['Historical data']
        
        for command, expected in zip(scenario['commands'], scenario['expected_responses']):
            response = await self.send_command(command)
            passed = self.validate_response(response, expected)
            
            result = {
                'scenario': scenario['name'],
                'command': command,
                'response': response,
                'expected': expected,
                'passed': passed,
                'timestamp': datetime.now().isoformat()
            }
            results.append(result)
            
            # Log result
            status = "✅ PASSED" if passed else "❌ FAILED"
            logger.info(f"{status} - Command: {command}")
            if not passed:
                logger.error(f"Expected: {expected}")
                logger.error(f"Got: {response}")
                
        return results
        
    async def run_all_tests(self):
        """Run all test scenarios"""
        try:
            await self.start()
            
            for scenario in TEST_SCENARIOS:
                results = await self.run_test_scenario(scenario)
                self.test_results.extend(results)
                
            await self.generate_report()
            
        except Exception as e:
            logger.error(f"Error running tests: {str(e)}")
        finally:
            await self.client.disconnect()
            
    async def generate_report(self):
        """Generate and save test report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"test_report_{timestamp}.json"
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['passed'])
        
        report = {
            'summary': {
                'timestamp': datetime.now().isoformat(),
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'success_rate': f"{(passed_tests/total_tests)*100:.2f}%"
            },
            'results': self.test_results,
            'errors': self.error_log
        }
        
        # Save detailed JSON report
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        # Generate human-readable summary
        summary_file = f"test_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write("=== Telegram Bot Test Summary ===\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Tests: {total_tests}\n")
            f.write(f"Passed: {passed_tests}\n")
            f.write(f"Failed: {total_tests - passed_tests}\n")
            f.write(f"Success Rate: {report['summary']['success_rate']}\n\n")
            
            # Group results by scenario
            for scenario in TEST_SCENARIOS:
                scenario_results = [r for r in self.test_results if r['scenario'] == scenario['name']]
                f.write(f"\nScenario: {scenario['name']}\n")
                f.write("-" * 50 + "\n")
                
                for result in scenario_results:
                    status = "✅ PASSED" if result['passed'] else "❌ FAILED"
                    f.write(f"{status} - {result['command']}\n")
                    if not result['passed']:
                        f.write(f"  Expected: {result['expected']}\n")
                        f.write(f"  Got: {result['response']}\n")
                        
            if self.error_log:
                f.write("\nErrors Encountered:\n")
                f.write("-" * 50 + "\n")
                for error in self.error_log:
                    f.write(f"Command: {error['command']}\n")
                    f.write(f"Error: {error['error']}\n")
                    f.write(f"Time: {error['timestamp']}\n\n")
                
        logger.info(f"Test report generated: {report_file}")
        logger.info(f"Test summary generated: {summary_file}")
        
def main():
    """Main entry point"""
    tester = TelegramBotTester()
    asyncio.run(tester.run_all_tests())
    
if __name__ == "__main__":
    main()
