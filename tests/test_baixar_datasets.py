import unittest
from unittest.mock import Mock

from baixar_datasets import DHSApiClient, DHSDownloader


class DHSApiClientTests(unittest.TestCase):
    def test_enrich_uses_country_metadata_and_matches_filename_case_insensitively(self):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "Data": [
                {
                    "FileName": "AOBR62dt.zip",
                    "FileSize": 1126527,
                    "FileType": "Births Raw",
                    "FileFormat": "Stata dataset (.dta)",
                }
            ]
        }
        session = Mock()
        session.get.return_value = response
        client = DHSApiClient(session=session)

        item = {"filename": "AOBR62DT.zip", "country_code": "AO"}
        enriched = client.enrich([item])

        self.assertEqual(enriched[0]["expected_size"], 1126527)
        self.assertEqual(enriched[0]["api_file_type"], "Births Raw")
        session.get.assert_called_once()
        self.assertEqual(session.get.call_args.kwargs["params"]["countryIds"], "AO")


class DHSDownloaderTests(unittest.TestCase):
    def test_403_and_429_are_retriable_rate_limit_responses(self):
        downloader = DHSDownloader(output_dir="dados-teste")

        self.assertTrue(downloader.is_retriable_status(403))
        self.assertTrue(downloader.is_retriable_status(429))
        self.assertFalse(downloader.is_retriable_status(404))

    def test_default_worker_count_is_one(self):
        self.assertEqual(DHSDownloader.DEFAULT_WORKERS, 1)

