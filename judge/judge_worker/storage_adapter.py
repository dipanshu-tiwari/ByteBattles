from config import SUBMISSION_BUCKET, TESTCASE_BUCKET
from api.app.core.storage import StorageServiceSubmissionCode, StorageServiceTestcases

class StorageAdapter:
    def __init__(self):
        self.submission_storage = StorageServiceSubmissionCode(SUBMISSION_BUCKET)
        self.testcase_storage = StorageServiceTestcases(TESTCASE_BUCKET)

    def read_submission_code(self, object_key: str) -> bytes:
        return self.submission_storage.get_file(object_key)

    def read_testcase_input(self, object_key: str) -> bytes:
        return self.testcase_storage.get_file(object_key)

    def read_testcase_output(self, object_key: str) -> bytes:
        return self.testcase_storage.get_file(object_key)