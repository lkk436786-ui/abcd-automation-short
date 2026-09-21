from shorts_engine.youtube import SHORT_HASHTAGS, _shorts_description, _video_metadata


def test_description_contains_multiple_short_hashtags():
    description = _shorts_description("Learn animal names with us!")

    assert description.startswith("Learn animal names with us!")
    assert description.count("#") >= 6
    assert "#Shorts" in description
    assert "#KidsLearning" in description


def test_metadata_marks_short_content_with_tags():
    metadata = _video_metadata("A title", "A description", "public")

    assert metadata["snippet"]["description"].endswith(SHORT_HASHTAGS)
    assert "Shorts" in metadata["snippet"]["tags"]
    assert metadata["status"]["selfDeclaredMadeForKids"] is True
