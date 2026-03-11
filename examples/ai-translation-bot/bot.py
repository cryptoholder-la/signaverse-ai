"""
AI Translation Bot
Autonomous bot that watches for new sign videos and provides translations
Integrates with the distributed Signaverse network
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Any, Optional
import sys
import os

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from core.ai.sign_language_pipeline import SignLanguagePipeline
from core.networking.p2p_network import P2PNetwork
from core.commit_engine.commit import CommitEngine
from core.delta_protocol.delta_ops import DeltaProtocol
from core.state.distributed_state import DistributedState

logger = logging.getLogger(__name__)


class TranslationBot:
    """AI bot that automatically translates sign language content"""
    
    def __init__(self, bot_id: str, agent_pubkey: str, bootstrap_peers: List[str] = None):
        self.bot_id = bot_id
        self.agent_pubkey = agent_pubkey
        
        # Initialize core components
        self.ai_pipeline = SignLanguagePipeline()
        self.p2p_network = P2PNetwork(agent_pubkey, bootstrap_peers)
        self.commit_engine = CommitEngine()
        self.distributed_state = DistributedState()
        
        # Bot configuration
        self.config = {
            "supported_languages": ["ASL", "BSL", "ISL"],
            "target_languages": ["en", "es", "fr", "de"],
            "auto_translate": True,
            "confidence_threshold": 0.7,
            "batch_size": 10,
            "processing_interval": 30  # seconds
        }
        
        # Bot state
        self.is_running = False
        self.processed_items = set()
        self.translation_queue = asyncio.Queue()
        self.stats = {
            "videos_processed": 0,
            "translations_created": 0,
            "errors": 0,
            "start_time": None
        }
        
        # Register network handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register network message handlers"""
        self.p2p_network.register_message_handler("new_sign_video", self._handle_new_sign_video)
        self.p2p_network.register_message_handler("translation_request", self._handle_translation_request)
        self.p2p_network.register_message_handler("bot_status", self._handle_status_request)
        
        # Register connection handlers
        self.p2p_network.register_connection_handler("peer_connected", self._handle_peer_connected)
        self.p2p_network.register_connection_handler("peer_disconnected", self._handle_peer_disconnected)
    
    async def start(self):
        """Start the translation bot"""
        if self.is_running:
            return
        
        logger.info(f"Starting translation bot {self.bot_id}")
        
        try:
            # Start AI pipeline
            # AI pipeline is initialized in constructor
            
            # Start P2P network
            await self.p2p_network.start(port=8766 + hash(self.bot_id) % 100)
            
            # Start background tasks
            self.is_running = True
            self.stats["start_time"] = time.time()
            
            asyncio.create_task(self._translation_processor())
            asyncio.create_task(self._network_monitor())
            asyncio.create_task(self._status_reporter())
            
            # Announce bot to network
            await self._announce_bot()
            
            logger.info(f"Translation bot {self.bot_id} started successfully")
            
        except Exception as e:
            logger.error(f"Error starting translation bot: {e}")
            raise
    
    async def stop(self):
        """Stop the translation bot"""
        if not self.is_running:
            return
        
        logger.info(f"Stopping translation bot {self.bot_id}")
        
        self.is_running = False
        
        # Stop P2P network
        await self.p2p_network.stop()
        
        # Log final statistics
        await self._log_final_stats()
        
        logger.info(f"Translation bot {self.bot_id} stopped")
    
    async def _handle_new_sign_video(self, message):
        """Handle new sign video upload"""
        try:
            video_data = message.payload
            video_hash = video_data.get("video_hash")
            
            # Check if already processed
            if video_hash in self.processed_items:
                return
            
            logger.info(f"New sign video detected: {video_hash}")
            
            # Add to processing queue
            await self.translation_queue.put({
                "type": "translate_video",
                "video_hash": video_hash,
                "video_data": video_data,
                "timestamp": time.time(),
                "source_peer": message.sender
            })
            
        except Exception as e:
            logger.error(f"Error handling new sign video: {e}")
    
    async def _handle_translation_request(self, message):
        """Handle explicit translation request"""
        try:
            request_data = message.payload
            video_hash = request_data.get("video_hash")
            target_language = request_data.get("target_language", "en")
            
            logger.info(f"Translation request for {video_hash} to {target_language}")
            
            # Add to processing queue
            await self.translation_queue.put({
                "type": "translate_request",
                "video_hash": video_hash,
                "target_language": target_language,
                "timestamp": time.time(),
                "source_peer": message.sender,
                "request_id": request_data.get("request_id")
            })
            
        except Exception as e:
            logger.error(f"Error handling translation request: {e}")
    
    async def _handle_status_request(self, message):
        """Handle status request from other peers"""
        try:
            status = await self._get_status()
            await self.p2p_network.send_message(
                message.sender,
                "bot_status_response",
                status
            )
        except Exception as e:
            logger.error(f"Error handling status request: {e}")
    
    async def _handle_peer_connected(self, peer_id):
        """Handle new peer connection"""
        logger.info(f"Peer connected: {peer_id}")
        
        # Announce bot capabilities
        await self.p2p_network.send_message(
            peer_id,
            "bot_announcement",
            {
                "bot_id": self.bot_id,
                "capabilities": ["sign_translation", "text_translation", "avatar_generation"],
                "supported_languages": self.config["supported_languages"],
                "target_languages": self.config["target_languages"]
            }
        )
    
    async def _handle_peer_disconnected(self, peer_id):
        """Handle peer disconnection"""
        logger.info(f"Peer disconnected: {peer_id}")
    
    async def _translation_processor(self):
        """Process translation queue"""
        while self.is_running:
            try:
                # Wait for translation task
                task = await asyncio.wait_for(
                    self.translation_queue.get(),
                    timeout=self.config["processing_interval"]
                )
                
                await self._process_translation_task(task)
                self.translation_queue.task_done()
                
            except asyncio.TimeoutError:
                # No tasks, continue
                continue
            except Exception as e:
                logger.error(f"Error in translation processor: {e}")
                self.stats["errors"] += 1
    
    async def _process_translation_task(self, task: Dict[str, Any]):
        """Process individual translation task"""
        try:
            task_type = task["type"]
            video_hash = task["video_hash"]
            
            if task_type == "translate_video":
                await self._auto_translate_video(video_hash, task["video_data"])
            elif task_type == "translate_request":
                await self._handle_explicit_translation_request(
                    video_hash, 
                    task["target_language"],
                    task["source_peer"],
                    task.get("request_id")
                )
            
            # Mark as processed
            self.processed_items.add(video_hash)
            
        except Exception as e:
            logger.error(f"Error processing translation task: {e}")
            self.stats["errors"] += 1
    
    async def _auto_translate_video(self, video_hash: str, video_data: Dict[str, Any]):
        """Automatically translate a sign video"""
        try:
            # Extract video path or use mock data
            video_path = video_data.get("video_path", f"/mock/path/{video_hash}.mp4")
            sign_language = video_data.get("language", "ASL")
            
            # Process video with AI pipeline
            result = await self.ai_pipeline.process_sign_video(video_path, sign_language)
            
            if result.confidence >= self.config["confidence_threshold"]:
                # Create translations for all target languages
                for target_lang in self.config["target_languages"]:
                    translation_result = await self.ai_pipeline.translate_text(
                        result.text,
                        "en",  # Assuming source text is English
                        target_lang
                    )
                    
                    # Create commit for translation
                    await self._create_translation_commit(
                        video_hash,
                        result.text,
                        translation_result.target_text,
                        sign_language,
                        target_lang,
                        translation_result.confidence
                    )
                
                self.stats["translations_created"] += len(self.config["target_languages"])
            
            self.stats["videos_processed"] += 1
            
            logger.info(f"Auto-translated video {video_hash}: {result.text}")
            
        except Exception as e:
            logger.error(f"Error auto-translating video: {e}")
            self.stats["errors"] += 1
    
    async def _handle_explicit_translation_request(self, video_hash: str, target_language: str, 
                                            source_peer: str, request_id: Optional[str]):
        """Handle explicit translation request"""
        try:
            # Get video data from distributed state
            video_data = self.distributed_state.get_state().get("sign_media", {}).get(video_hash)
            if not video_data:
                # Request video data from network
                await self.p2p_network.send_message(
                    None,  # Broadcast
                    "video_data_request",
                    {"video_hash": video_hash}
                )
                return
            
            # Process video
            video_path = video_data.get("video_path", f"/mock/path/{video_hash}.mp4")
            sign_language = video_data.get("language", "ASL")
            
            result = await self.ai_pipeline.process_sign_video(video_path, sign_language)
            
            # Translate to target language
            translation_result = await self.ai_pipeline.translate_text(
                result.text,
                "en",
                target_language
            )
            
            # Send response
            response = {
                "request_id": request_id,
                "video_hash": video_hash,
                "source_text": result.text,
                "target_text": translation_result.target_text,
                "target_language": target_language,
                "confidence": translation_result.confidence,
                "processing_bot": self.bot_id
            }
            
            await self.p2p_network.send_message(
                source_peer,
                "translation_response",
                response
            )
            
            # Create commit for translation
            await self._create_translation_commit(
                video_hash,
                result.text,
                translation_result.target_text,
                sign_language,
                target_language,
                translation_result.confidence
            )
            
            logger.info(f"Handled translation request for {video_hash}")
            
        except Exception as e:
            logger.error(f"Error handling explicit translation request: {e}")
            self.stats["errors"] += 1
    
    async def _create_translation_commit(self, video_hash: str, source_text: str, 
                                    target_text: str, source_lang: str, 
                                    target_lang: str, confidence: float):
        """Create a commit for the translation"""
        try:
            # Create translation entry
            translation_id = f"trans_{int(time.time())}_{hash(video_hash) % 10000}"
            
            # Create deltas for the translation
            deltas = [
                DeltaProtocol.insert("/translations", {
                    "id": translation_id,
                    "video_hash": video_hash,
                    "source_text": source_text,
                    "target_text": target_text,
                    "source_language": source_lang,
                    "target_language": target_lang,
                    "translator": self.agent_pubkey,
                    "confidence": confidence,
                    "timestamp": time.time(),
                    "bot_generated": True
                })
            ]
            
            # Create commit
            commit = self.commit_engine.create_commit(
                deltas,
                message=f"AI translation: {source_text} → {target_text}"
            )
            
            # Publish to network
            await self.p2p_network.send_message(
                None,  # Broadcast
                "new_translation",
                {
                    "commit_id": commit.commit_id,
                    "translation_id": translation_id,
                    "video_hash": video_hash,
                    "bot_id": self.bot_id
                }
            )
            
            # Apply to distributed state
            await self.distributed_state.apply_commit({
                "commit_id": commit.commit_id,
                "author": self.agent_pubkey,
                "timestamp": time.time(),
                "deltas": [delta.to_dict() for delta in deltas],
                "message": f"AI translation: {source_text} → {target_text}"
            })
            
        except Exception as e:
            logger.error(f"Error creating translation commit: {e}")
    
    async def _announce_bot(self):
        """Announce bot presence to network"""
        announcement = {
            "bot_id": self.bot_id,
            "bot_type": "translation",
            "capabilities": ["sign_translation", "text_translation", "avatar_generation"],
            "supported_languages": self.config["supported_languages"],
            "target_languages": self.config["target_languages"],
            "confidence_threshold": self.config["confidence_threshold"],
            "auto_translate": self.config["auto_translate"]
        }
        
        await self.p2p_network.send_message(
            None,  # Broadcast
            "bot_announcement",
            announcement
        )
    
    async def _network_monitor(self):
        """Monitor network status and health"""
        while self.is_running:
            try:
                # Get network stats
                stats = self.p2p_network.get_network_stats()
                
                if stats["connected_peers"] == 0:
                    logger.warning("No connected peers - bot may be isolated")
                
                # Log periodic status
                if int(time.time()) % 300 == 0:  # Every 5 minutes
                    logger.info(f"Network status: {stats['connected_peers']} peers, "
                               f"{stats['messages_received']} messages received")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in network monitor: {e}")
                await asyncio.sleep(10)
    
    async def _status_reporter(self):
        """Periodically report bot status"""
        while self.is_running:
            try:
                status = await self._get_status()
                
                # Log status
                logger.info(f"Bot status: {status['videos_processed']} videos processed, "
                           f"{status['translations_created']} translations created")
                
                await asyncio.sleep(300)  # Report every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in status reporter: {e}")
                await asyncio.sleep(30)
    
    async def _get_status(self) -> Dict[str, Any]:
        """Get current bot status"""
        uptime = time.time() - self.stats["start_time"] if self.stats["start_time"] else 0
        
        return {
            "bot_id": self.bot_id,
            "is_running": self.is_running,
            "uptime": uptime,
            "stats": self.stats.copy(),
            "queue_size": self.translation_queue.qsize(),
            "processed_items": len(self.processed_items),
            "config": self.config.copy()
        }
    
    async def _log_final_stats(self):
        """Log final statistics when stopping"""
        status = await self._get_status()
        
        logger.info("=" * 50)
        logger.info("TRANSLATION BOT FINAL STATISTICS")
        logger.info("=" * 50)
        logger.info(f"Bot ID: {status['bot_id']}")
        logger.info(f"Total Uptime: {status['uptime']:.2f} seconds")
        logger.info(f"Videos Processed: {status['stats']['videos_processed']}")
        logger.info(f"Translations Created: {status['stats']['translations_created']}")
        logger.info(f"Errors: {status['stats']['errors']}")
        logger.info(f"Items Processed: {status['processed_items']}")
        logger.info("=" * 50)


async def main():
    """Main entry point for the translation bot"""
    # Configuration
    bot_id = f"translation_bot_{int(time.time())}"
    agent_pubkey = f"bot_pubkey_{hash(bot_id) % 1000000}"
    
    # Bootstrap peers (would be configured in production)
    bootstrap_peers = [
        "ws://localhost:8765",
        "ws://signaverse-bootstrap1.example.com:8765",
        "ws://signaverse-bootstrap2.example.com:8765"
    ]
    
    # Create and start bot
    bot = TranslationBot(bot_id, agent_pubkey, bootstrap_peers)
    
    try:
        await bot.start()
        
        # Keep running until interrupted
        while bot.is_running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await bot.stop()


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run bot
    asyncio.run(main())
