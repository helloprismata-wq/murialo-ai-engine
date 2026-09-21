TRAIN_RAW = [
    ("Saya adalah seorang Software Engineer di PT Telkom Indonesia. Saya lulus dari Universitas Indonesia dengan gelar S1 Teknik Informatika. Keahlian saya meliputi Python, Django, dan PostgreSQL.",
     {"JOB_TITLE": ["Software Engineer"], "COMPANY": ["PT Telkom Indonesia"], "EDUCATION": ["Universitas Indonesia"], "DEGREE": ["S1 Teknik Informatika"], "SKILL": ["Python", "Django", "PostgreSQL"]}),

    ("Bekerja sebagai Data Scientist di Tokopedia selama 3 tahun. Latar belakang pendidikan S2 Ilmu Komputer dari Institut Teknologi Bandung. Terbiasa menggunakan Machine Learning, TensorFlow, dan scikit-learn.",
     {"JOB_TITLE": ["Data Scientist"], "COMPANY": ["Tokopedia"], "DEGREE": ["S2 Ilmu Komputer"], "EDUCATION": ["Institut Teknologi Bandung"], "SKILL": ["Machine Learning", "TensorFlow", "scikit-learn"]}),

    ("Pengalaman 5 tahun sebagai Backend Developer di Gojek. Lulusan S1 Sistem Informasi Universitas Gadjah Mada. Tech stack: Node.js, Express, MongoDB, dan AWS.",
     {"JOB_TITLE": ["Backend Developer"], "COMPANY": ["Gojek"], "DEGREE": ["S1 Sistem Informasi"], "EDUCATION": ["Universitas Gadjah Mada"], "SKILL": ["Node.js", "Express", "MongoDB", "AWS"]}),

    ("Saya UI/UX Designer yang pernah bekerja di Traveloka. Menguasai Figma, Adobe Illustrator, dan HTML CSS. Lulusan Desain Komunikasi Visual dari Binus University.",
     {"JOB_TITLE": ["UI/UX Designer"], "COMPANY": ["Traveloka"], "SKILL": ["Figma", "Adobe Illustrator", "HTML CSS"], "DEGREE": ["Desain Komunikasi Visual"], "EDUCATION": ["Binus University"]}),
     
    ("Frontend Engineer dengan pengalaman menggunakan React dan Vue. Sebelumnya bekerja di Shopee Indonesia. Pendidikan D3 Teknik Komputer dari Politeknik Negeri Jakarta.",
     {"JOB_TITLE": ["Frontend Engineer"], "SKILL": ["React", "Vue"], "COMPANY": ["Shopee Indonesia"], "DEGREE": ["D3 Teknik Komputer"], "EDUCATION": ["Politeknik Negeri Jakarta"]}),
     
    ("DevOps Engineer di Bukalapak. Ahli dalam Kubernetes, Docker, dan CI/CD. Gelar S1 Teknik Elektro dari Universitas Diponegoro.",
     {"JOB_TITLE": ["DevOps Engineer"], "COMPANY": ["Bukalapak"], "SKILL": ["Kubernetes", "Docker", "CI/CD"], "DEGREE": ["S1 Teknik Elektro"], "EDUCATION": ["Universitas Diponegoro"]}),
     
    ("Mobile Developer (Android/iOS) menggunakan Flutter dan Dart. Lulusan S1 Informatika dari ITS Surabaya. Pernah magang di Ruangguru.",
     {"JOB_TITLE": ["Mobile Developer"], "SKILL": ["Flutter", "Dart"], "DEGREE": ["S1 Informatika"], "EDUCATION": ["ITS Surabaya"], "COMPANY": ["Ruangguru"]}),
     
    ("Data Analyst berpengalaman dengan SQL, Tableau, dan Excel. Lulus S1 Statistika di Institut Pertanian Bogor. Bekerja saat ini di Bank BCA.",
     {"JOB_TITLE": ["Data Analyst"], "SKILL": ["SQL", "Tableau", "Excel"], "DEGREE": ["S1 Statistika"], "EDUCATION": ["Institut Pertanian Bogor"], "COMPANY": ["Bank BCA"]}),
]

with open(r"d:\program skripsi\resume-parser\resume\training\training_data.py", "w") as f:
    f.write("TRAIN_DATA = [\n")
    for text, ents_dict in TRAIN_RAW:
        entities = []
        for label, substrings in ents_dict.items():
            for sub in substrings:
                start = text.find(sub)
                if start != -1:
                    end = start + len(sub)
                    entities.append((start, end, label))
        
        # Sort by start to avoid issues
        entities = sorted(entities, key=lambda x: x[0])
        
        f.write(f'    ("{text}",\n')
        f.write(f'     {{"entities": {entities}}}),\n')
    f.write("]\n")

print("Generated training_data.py")
