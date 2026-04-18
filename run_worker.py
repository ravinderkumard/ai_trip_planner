# run_worker.py

from worker import TravelAgentWorker
from dotenv import load_dotenv
load_dotenv()
if __name__ == "__main__":
    worker = TravelAgentWorker()
    worker.start()