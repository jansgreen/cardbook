from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from cardbookweb.test_utils import make_user, make_white_card_job
from jobcards.models import Specialty, WhiteCardJob


def tiny_gif(name="card.gif"):
    return SimpleUploadedFile(
        name,
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;",
        content_type="image/gif",
    )


class WhiteCardJobPhysicalImportTests(APITestCase):
    def test_create_white_card_job_with_physical_card_images(self):
        user = make_user("jobscanuser", registration_intent="job")
        specialty = Specialty.objects.create(name="Soldador", category="Oficios")
        self.client.force_authenticate(user)

        response = self.client.post(
            "/api/v1/jobcards/",
            {
                "title": "Soldador disponible",
                "phone_number": "9172135087",
                "address": "Paterson, NJ",
                "specialty": specialty.id,
                "short_description": "Soldador con experiencia en estructuras metalicas.",
                "availability_note": "Tiempo completo",
                "is_available": True,
                "is_physical_card_imported": True,
                "physical_card_front_image": tiny_gif("front.gif"),
                "physical_card_back_image": tiny_gif("back.gif"),
            },
            format="multipart",
            HTTP_HOST="127.0.0.1:8000",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        card = WhiteCardJob.objects.get(user=user)
        self.assertTrue(card.is_physical_card_imported)
        self.assertTrue(card.physical_card_front_image.name)
        self.assertTrue(card.physical_card_back_image.name)
        self.assertIn("physical_card_front_image", response.data["data"])
        self.assertIn("physical_card_back_image", response.data["data"])

    def test_mobile_jobs_serializes_physical_card_import_fields(self):
        user = make_user("mobilejobviewer")
        job_user = make_user("jobwithscan", registration_intent="job")
        make_white_card_job(
            user=job_user,
            is_physical_card_imported=True,
            physical_card_front_image=tiny_gif("front.gif"),
        )
        self.client.force_authenticate(user)

        response = self.client.get("/api/v1/mobile/jobs/", HTTP_HOST="127.0.0.1:8000")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        jobs = response.data["data"]["available_jobs"]
        imported = [item for item in jobs if item["username"] == "jobwithscan"][0]
        self.assertTrue(imported["is_physical_card_imported"])
        self.assertTrue(imported["physical_card_front_image"])
