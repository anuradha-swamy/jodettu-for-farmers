"""
Master Data Service
Handles Animal Types and Breeds stored in PostgreSQL.
"""

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_

from models.sql_models import AnimalType, Breed


class MasterDataService:
    # ---------------------------------------------------------
    # READ APIs
    # ---------------------------------------------------------

    async def get_animal_types(self, db: AsyncSession) -> List[str]:
        """
        Retrieves a list of active animal type names from PostgreSQL.
        """
        query = (
            select(AnimalType.name)
            .where(AnimalType.is_active == True)
            .order_by(AnimalType.name)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_breeds_by_animal_type(
        self, db: AsyncSession, animal_type: str
    ) -> List[str]:
        """
        Retrieves a list of active breed names for a given animal type.
        """
        query = (
            select(Breed.name)
            .join(AnimalType)
            .where(
                and_(
                    AnimalType.name == animal_type.lower(),
                    AnimalType.is_active == True,
                    Breed.is_active == True,
                )
            )
            .order_by(Breed.name)
        )
        result = await db.execute(query)
        return result.scalars().all()

    # ---------------------------------------------------------
    # CREATE APIs
    # ---------------------------------------------------------

    async def create_animal_type(self, db: AsyncSession, type_name: str):
        """
        Creates a new animal type in PostgreSQL.
        """
        type_name = type_name.lower()

        result = await db.execute(
            select(AnimalType).where(AnimalType.name == type_name)
        )
        existing = result.scalars().first()

        if existing:
            return existing

        new_type = AnimalType(name=type_name)
        db.add(new_type)
        await db.commit()
        await db.refresh(new_type)
        return new_type

    async def create_breed(
        self, db: AsyncSession, type_name: str, breed_name: str
    ):
        """
        Creates a new breed for an animal type in PostgreSQL.
        """
        type_name = type_name.lower()

        result = await db.execute(
            select(AnimalType).where(AnimalType.name == type_name)
        )
        animal_type = result.scalars().first()

        if not animal_type:
            raise ValueError(f"Animal type '{type_name}' not found")

        result = await db.execute(
            select(Breed).where(
                Breed.name == breed_name,
                Breed.animal_type_id == animal_type.id,
            )
        )
        existing = result.scalars().first()

        if existing:
            return existing

        new_breed = Breed(
            name=breed_name,
            animal_type_id=animal_type.id,
        )
        db.add(new_breed)
        await db.commit()
        await db.refresh(new_breed)
        return new_breed

    # ---------------------------------------------------------
    # STARTUP INITIALIZER (🔥 REQUIRED 🔥)
    # ---------------------------------------------------------

    @staticmethod
    async def initialize_default_data(db: AsyncSession) -> None:
        """
        Initializes default animal types and breeds.
        Safe to run multiple times.
        """

        default_data = {
            "cow": ["Gir", "Sahiwal", "Jersey"],
            "buffalo": ["Murrah", "Surti"],
            "goat": ["Boer", "Saanen"],
            "sheep": ["Merino"],
            "ox": ["Hallikar"],
        }

        for animal_name, breeds in default_data.items():
            # Check animal type
            result = await db.execute(
                select(AnimalType).where(AnimalType.name == animal_name)
            )
            animal_type = result.scalars().first()

            if not animal_type:
                animal_type = AnimalType(name=animal_name)
                db.add(animal_type)
                await db.flush()  # get ID without commit

            for breed_name in breeds:
                result = await db.execute(
                    select(Breed).where(
                        Breed.name == breed_name,
                        Breed.animal_type_id == animal_type.id,
                    )
                )
                exists = result.scalars().first()

                if not exists:
                    db.add(
                        Breed(
                            name=breed_name,
                            animal_type_id=animal_type.id,
                        )
                    )

        await db.commit()


# Singleton instance
master_data_service = MasterDataService()
